"""TAP schema management service layer.

This module provides the service layer for TAP schema management operations.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from felis.datamodel import Schema
from felis.db.database_context import DatabaseContext, create_database_context
from felis.tap_schema import DataLoader, MetadataInserter, TableManager
from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import URL
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.schema import CreateSchema, DropSchema

from repertoire.exceptions import (
    TAPSchemaNotFoundError,
    TAPSchemaValidationError,
)
from repertoire.schema.version import TAPSchemaVersion
from repertoire.storage.tap_schema import TAPSchemaStorage

if TYPE_CHECKING:
    from structlog.stdlib import BoundLogger

__all__ = ["TAPSchemaService"]

STAGING_SCHEMA = "tap_schema_staging"  # Temporary schema for loading new data
PRODUCTION_SCHEMA = "tap_schema"  # Live schema used by TAP
TEMP_SCHEMA = "tap_schema_temp"  # Temporary name during swap


class TAPSchemaService:
    """Manage TAP_SCHEMA updates and operations.

    Orchestrates the workflow for updating TAP_SCHEMA, including:
    - Initializing staging schema
    - Downloading and loading schema files
    - Validating the staged data
    - Swapping staging to production

    Parameters
    ----------
    engine
        Async SQLAlchemy engine for database operations.
    logger
        Logger for debug messages and errors.
    storage
        The underlying schema storage layer for downloading and extracting
        schemas.
    schema_version
        Version identifier for schemas to load.
    schema_list
        List of schema names to load.
    source_url_template
        URL template with {version} placeholder for schema downloads.
    database_password
        Optional password for database connections (used for sync engine).
    table_postfix
        Postfix for TAP_SCHEMA table names (default: "11").
    extensions_path
        Optional path to YAML file with TAP_SCHEMA extensions.
    """

    def __init__(
        self,
        *,
        engine: AsyncEngine,
        logger: BoundLogger,
        storage: TAPSchemaStorage,
        schema_version: str,
        schema_list: list[str],
        source_url_template: str,
        database_password: str | None = None,
        table_postfix: str = "11",
        extensions_path: str | None = None,
    ) -> None:
        self._engine = engine
        self._logger = logger
        self._storage = storage
        self._schema_version = schema_version
        self._schema_list = schema_list
        self._source_url_template = source_url_template
        self._database_password = database_password
        self._table_postfix = table_postfix
        self._extensions_path = extensions_path

    async def update(self, work_dir: Path | None = None) -> None:
        """Execute complete TAP_SCHEMA update workflow.

        Initialize -> download -> load -> validate -> swap

        Parameters
        ----------
        work_dir
            Working directory for temporary files. If not provided, a
            temporary directory will be created and cleaned up automatically.

        Raises
        ------
        TAPSchemaDownloadError
            If schema download fails.
        TAPSchemaValidationError
            If schema validation fails.
        """
        if work_dir is None:
            with tempfile.TemporaryDirectory() as tmpdir:
                work_dir = Path(tmpdir)
                await self._execute_update(work_dir)
        else:
            await self._execute_update(work_dir)

    async def _execute_update(self, work_dir: Path) -> None:
        """Execute the update workflow with a given work directory.

        Parameters
        ----------
        work_dir
            Working directory for temporary files.
        """
        self._logger.info(
            "Starting TAP schema update execution",
            schema_version=self._schema_version,
            schemas=self._schema_list,
            work_dir=str(work_dir),
        )

        await self._initialize_schemas()
        sync_url_str = self._create_sync_url()
        mgr = self._create_table_manager(sync_url_str)
        with create_database_context(sync_url_str, mgr.metadata) as db_ctx:
            self._initialize_database(mgr, db_ctx)

            self._logger.info(
                "Downloading and extracting schemas",
                schema_version=self._schema_version,
                source_url_template=self._source_url_template,
            )
            yaml_dir = await self._storage.download_and_extract(
                self._schema_version,
                self._source_url_template,
                work_dir,
            )
            self._logger.info("Schemas extracted", yaml_dir=str(yaml_dir))

            self._logger.info(
                "Loading schemas into database",
                schemas_to_load=self._schema_list,
            )
            self._load_schemas(yaml_dir, mgr, db_ctx)
            self._logger.info("Schemas loaded successfully")

        await self._record_version()
        await self._create_views()
        await self._validate_staging()
        await self._swap_schemas()

    async def _initialize_schemas(self) -> None:
        """Initialize required schemas in the database."""
        self._logger.info("Initializing staging schema", schema=STAGING_SCHEMA)
        async with self._engine.begin() as conn:
            await conn.execute(
                DropSchema(STAGING_SCHEMA, cascade=True, if_exists=True)
            )
            await conn.execute(CreateSchema(STAGING_SCHEMA))
        self._logger.info("Staging schema initialized")

    def _create_sync_url(self) -> str:
        """Create a synchronous database URL from the async engine URL.

        Returns
        -------
        str
            Synchronous PostgreSQL database URL string.
        """
        async_url = make_url(str(self._engine.url))
        sync_url = URL.create(
            drivername="postgresql+psycopg2",
            username=async_url.username,
            password=self._database_password or async_url.password,
            host=async_url.host,
            port=async_url.port,
            database=async_url.database,
        )

        # Use render_as_string to properly encode the password
        return sync_url.render_as_string(hide_password=False)

    def _create_table_manager(self, sync_url_str: str) -> TableManager:
        """Create a TableManager with TAP_SCHEMA metadata loaded from YAML.

        Parameters
        ----------
        sync_url_str
            String representation of the sync database URL.

        Returns
        -------
        TableManager
            Table manager with metadata loaded from extensions YAML.
        """
        # Use custom extensions path if provided, otherwise fall back to the
        # default TAP_SCHEMA extensions configuration bundled with felis.
        # The resource:// URI references a file within the felis package.
        extensions_path = (
            self._extensions_path
            or "resource://felis/config/tap_schema/tap_schema_extensions.yaml"
        )

        return TableManager(
            engine_url=sync_url_str,
            schema_name=STAGING_SCHEMA,
            table_name_postfix=self._table_postfix,
            extensions_path=extensions_path,
        )

    def _initialize_database(
        self, mgr: TableManager, db_ctx: DatabaseContext
    ) -> None:
        """Initialize TAP_SCHEMA database tables and insert metadata.

        Parameters
        ----------
        mgr
            Table manager with loaded metadata.
        db_ctx
            Database context for operations.
        """
        self._logger.info(
            "Initializing TAP_SCHEMA tables",
            schema=STAGING_SCHEMA,
            table_postfix=self._table_postfix,
        )

        mgr.initialize_database(db_ctx)
        inserter = MetadataInserter(mgr, db_ctx)
        inserter.insert_metadata()

        self._logger.info("TAP_SCHEMA tables initialized")

    def _load_schemas(
        self,
        yaml_dir: Path,
        mgr: TableManager,
        db_ctx: DatabaseContext,
    ) -> None:
        """Load schemas from YAML files.

        Parameters
        ----------
        yaml_dir
            Directory containing schema YAML files.
        mgr
            Table manager for database operations.
        db_ctx
            Database context for operations.

        Raises
        ------
        TAPSchemaNotFoundError
            If a required schema file is not found.
        """
        self._logger.info(
            "Starting schema loading",
            schemas_count=len(self._schema_list),
            yaml_dir=str(yaml_dir),
        )

        for i, schema_name in enumerate(self._schema_list, 1):
            schema_file = yaml_dir / f"{schema_name}.yaml"

            if not schema_file.exists():
                available = sorted([f.stem for f in yaml_dir.glob("*.yaml")])
                self._logger.error(
                    "Schema file not found",
                    schema_name=schema_name,
                    schema_file=str(schema_file),
                    available=available,
                )
                raise TAPSchemaNotFoundError(schema_name, available)

            self._logger.info(
                "Loading schema",
                schema_number=f"{i}/{len(self._schema_list)}",
                schema_name=schema_name,
                schema_file=str(schema_file),
            )

            felis_schema = Schema.from_uri(
                str(schema_file),
                context={
                    "id_generation": True,
                    "force_unbounded_arraysize": True,
                },
            )

            loader = DataLoader(
                schema=felis_schema,
                mgr=mgr,
                db_context=db_ctx,
            )
            loader.load()

            self._logger.info(
                "Schema loaded successfully", schema_name=schema_name
            )

    async def _create_views(self) -> None:
        """Create views for TAP_SCHEMA tables."""
        self._logger.info("Creating TAP_SCHEMA views", schema=STAGING_SCHEMA)

        views = {
            "schemas": f"schemas{self._table_postfix}",
            "tables": f"tables{self._table_postfix}",
            "columns": f"columns{self._table_postfix}",
            "keys": f"keys{self._table_postfix}",
            "key_columns": f"key_columns{self._table_postfix}",
        }

        async with self._engine.begin() as conn:
            for view_name, table_name in views.items():
                await conn.execute(
                    text(
                        f"CREATE "  # noqa: S608
                        f"OR REPLACE VIEW {STAGING_SCHEMA}.{view_name} AS "
                        f"SELECT * FROM {STAGING_SCHEMA}.{table_name}"
                    )
                )

        self._logger.info("All views created successfully", count=len(views))

    async def _record_version(self) -> None:
        """Record schema version in version table."""
        self._logger.info(
            "Recording schema version", version=self._schema_version
        )

        async with self._engine.begin() as conn:
            await conn.run_sync(TAPSchemaVersion.metadata.create_all)
            stmt = (
                insert(TAPSchemaVersion)
                .values(version=self._schema_version, loaded_at=func.now())
                .on_conflict_do_update(
                    index_elements=["version"],
                    set_={"loaded_at": func.now()},
                )
            )
            await conn.execute(stmt)

        self._logger.info(
            "Schema version recorded", version=self._schema_version
        )

    async def _validate_staging(self) -> None:
        """Validate staging schema has expected data.

        Raises
        ------
        TAPSchemaValidationError
            If validation fails.
        """
        self._logger.info(
            "Validating staging schema",
            schema=STAGING_SCHEMA,
            expected_count=len(self._schema_list),
        )

        async with self._engine.begin() as conn:
            schemas_table = f"schemas{self._table_postfix}"
            result = await conn.execute(
                text(
                    f"SELECT COUNT(*) FROM {STAGING_SCHEMA}."  # noqa: S608
                    f"{schemas_table} WHERE schema_name != 'tap_schema'"
                )
            )
            count = result.scalar()

            self._logger.info(
                "Schemas table row count",
                table=schemas_table,
                count=count,
                expected=len(self._schema_list),
            )

            if count != len(self._schema_list):
                raise TAPSchemaValidationError(
                    f"Expected {len(self._schema_list)} schemas "
                    f"but found {count}",
                    schema_version=self._schema_version,
                )

            self._logger.info(
                "Validation passed",
                schemas_loaded=count,
            )

    async def _swap_schemas(self) -> None:
        """Swap staging and live schemas.

        Process:
          1. Rename production -> temp
          2. Rename staging -> production
          3. Rename temp -> staging
        """
        async with self._engine.begin() as conn:
            result = await conn.execute(
                text("""
                    SELECT schema_name FROM information_schema.schemata
                    WHERE schema_name = :schema_name
                """),
                {"schema_name": PRODUCTION_SCHEMA},
            )
            prod_exists = result.scalar() is not None

            self._logger.info(
                "Production schema status",
                schema=PRODUCTION_SCHEMA,
                exists=prod_exists,
            )

            if not prod_exists:
                self._logger.info(
                    "First deployment: renaming staging to production",
                    from_schema=STAGING_SCHEMA,
                    to_schema=PRODUCTION_SCHEMA,
                )

                await conn.execute(
                    text(
                        f"ALTER SCHEMA {STAGING_SCHEMA} "
                        f"RENAME TO {PRODUCTION_SCHEMA}"
                    )
                )
                self._logger.info("Schema renamed successfully")
            else:
                self._logger.info(
                    "Existing deployment detected, performing swap",
                    production=PRODUCTION_SCHEMA,
                    staging=STAGING_SCHEMA,
                    temp=TEMP_SCHEMA,
                )

                await conn.execute(
                    text(
                        f"ALTER SCHEMA {PRODUCTION_SCHEMA} "
                        f"RENAME TO {TEMP_SCHEMA}"
                    )
                )

                await conn.execute(
                    text(
                        f"ALTER SCHEMA {STAGING_SCHEMA} "
                        f"RENAME TO {PRODUCTION_SCHEMA}"
                    )
                )

                await conn.execute(
                    text(
                        f"ALTER SCHEMA {TEMP_SCHEMA} "
                        f"RENAME TO {STAGING_SCHEMA}"
                    )
                )

                self._logger.info("Schema swap completed successfully")

        self._logger.info("Schema swap complete, TAP_SCHEMA is now live")
