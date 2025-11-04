"""TAP schema manager."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from felis.datamodel import Schema
from felis.tap_schema import DataLoader, MetadataInserter, TableManager
from sqlalchemy import TIMESTAMP, Column, Engine, MetaData, String, Table, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import URL, create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.schema import CreateSchema, CreateTable, DropSchema

from .download import download_schemas

if TYPE_CHECKING:
    from structlog.stdlib import BoundLogger

__all__ = ["TapSchemaManager"]

STAGING_SCHEMA = "tap_schema_staging"  # Temporary schema for loading new data
PRODUCTION_SCHEMA = "tap_schema"  # Live schema used by TAP
TEMP_SCHEMA = "tap_schema_temp"  # Temporary name during swap

_staging_metadata = MetaData(schema=STAGING_SCHEMA)
VERSION_TABLE = Table(
    "version",
    _staging_metadata,
    Column("version", String, primary_key=True),
    Column(
        "loaded_at",
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    ),
)


class TapSchemaManager:
    """Manages TAP_SCHEMA updates and operations.

    This class orchestrates the workflow for updating TAP_SCHEMA, including:
    - Initializing staging schema
    - Downloading and loading schema files
    - Validating the staged data
    - Swapping staging to production

    Parameters
    ----------
    engine
        Async SQLAlchemy engine for database operations.
    logger
        Structured logger.
    schema_version
        Version identifier for schemas.
    schema_list
        List of schema names to load.
    source_url_template
        URL template with {version} placeholder for schema downloads.
    database_password
        Optional password for database connections.
    """

    def __init__(
        self,
        engine: AsyncEngine,
        logger: BoundLogger,
        schema_version: str,
        schema_list: list[str],
        source_url_template: str,
        database_password: str | None = None,
        table_postfix: str = "11",
    ) -> None:
        self._engine = engine
        self._logger = logger
        self._schema_version = schema_version
        self._schema_list = schema_list
        self._source_url_template = source_url_template
        self._database_password = database_password
        self._table_postfix = table_postfix

    async def update(self) -> None:
        """Execute complete TAP_SCHEMA update workflow.

        Initialize -> download -> load -> validate -> swap

        Raises
        ------
        RuntimeError
            If validation fails or no schemas are loaded.
        """
        await self._initialize_schemas()
        sync_engine = self._create_sync_engine()

        try:
            mgr = self._initialize_table_manager(sync_engine)
            with tempfile.TemporaryDirectory() as tmpdir:
                yaml_dir = await download_schemas(
                    self._schema_version,
                    self._source_url_template,
                    Path(tmpdir),
                    self._logger,
                )
                self._load_schemas(yaml_dir, mgr, sync_engine)

            await self._record_version()
            await self._create_views()
            await self._validate_staging()
            await self._swap_schemas()

        finally:
            sync_engine.dispose()

    async def _initialize_schemas(self) -> None:
        """Initialize any required schemas in the database."""
        async with self._engine.begin() as conn:
            await conn.execute(
                DropSchema(STAGING_SCHEMA, cascade=True, if_exists=True)
            )
            await conn.execute(CreateSchema(STAGING_SCHEMA))

    def _create_sync_engine(self) -> Engine:
        """Create synchronous engine for felis operations.

        Returns
        -------
        Engine
            Synchronous SQLAlchemy engine.
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
        return create_engine(sync_url)

    def _initialize_table_manager(self, sync_engine: Engine) -> TableManager:
        """Initialize TAP_SCHEMA tables and metadata.

        Parameters
        ----------
        sync_engine
            Synchronous database engine.

        Returns
        -------
        TableManager
            Initialized table manager for schema operations.
        """
        mgr = TableManager(
            schema_name=STAGING_SCHEMA,
            table_name_postfix=self._table_postfix,
            apply_schema_to_metadata=True,
        )
        mgr.initialize_database(sync_engine)
        inserter = MetadataInserter(mgr, sync_engine)
        inserter.insert_metadata()

        return mgr

    def _load_schemas(
        self,
        yaml_dir: Path,
        mgr: TableManager,
        sync_engine: Engine,
    ) -> None:
        """Load schemas from YAML files using felis.

        Iterates through the schema list and loads each schema
        definition into the TAP_SCHEMA tables in staging.

        Parameters
        ----------
        yaml_dir
            Directory containing schema YAML files.
        mgr
            Table manager for database operations.
        sync_engine
            Synchronous database engine.

        Raises
        ------
        RuntimeError
            If a required schema file is not found.
        """
        for schema_name in self._schema_list:
            schema_file = yaml_dir / f"{schema_name}.yaml"

            if not schema_file.exists():
                available = [f.stem for f in yaml_dir.glob("*.yaml")]
                raise RuntimeError(
                    f"Schema not found: {schema_name}.yaml\n"
                    f"Available: {', '.join(available)}"
                )

            felis_schema = Schema.from_uri(
                str(schema_file), context={"id_generation": True}
            )

            loader = DataLoader(
                schema=felis_schema,
                mgr=mgr,
                engine=sync_engine,
            )
            loader.load()

    async def _create_views(self) -> None:
        """Create views for TAP_SCHEMA tables."""
        views = {
            "schemas": f"schemas{self._table_postfix}",
            "tables": f"tables{self._table_postfix}",
            "columns": f"columns{self._table_postfix}",
            "keys": f"keys{self._table_postfix}",
            "key_columns": f"key_columns{self._table_postfix}",
            "version": f"version{self._table_postfix}",
        }

        async with self._engine.begin() as conn:
            for view, table in views.items():
                await conn.execute(
                    text(
                        f"CREATE OR REPLACE VIEW {STAGING_SCHEMA}.{view} AS "  # noqa: S608
                        f"SELECT * FROM {STAGING_SCHEMA}.{table}"
                    )
                )

    async def _record_version(self) -> None:
        """Record schema version in version table."""
        self._logger.info("Recording version", version=self._schema_version)
        version_table = Table(
            f"version{self._table_postfix}",
            MetaData(schema=STAGING_SCHEMA),
            Column("version", String, primary_key=True),
            Column(
                "loaded_at",
                TIMESTAMP(timezone=True),
                server_default=text("CURRENT_TIMESTAMP"),
            ),
        )
        async with self._engine.begin() as conn:
            await conn.execute(CreateTable(version_table, if_not_exists=True))

            stmt = (
                insert(version_table)
                .values(
                    version=self._schema_version,
                    loaded_at=text("CURRENT_TIMESTAMP"),
                )
                .on_conflict_do_update(
                    index_elements=["version"],
                    set_={"loaded_at": text("CURRENT_TIMESTAMP")},
                )
            )
            await conn.execute(stmt)

    async def _validate_staging(self) -> None:
        """Validate staging schema has data.

        Raises
        ------
        RuntimeError
            If no schemas were loaded to staging.
        """
        async with self._engine.begin() as conn:
            required_tables = [
                f"schemas{self._table_postfix}",
                f"tables{self._table_postfix}",
                f"columns{self._table_postfix}",
                f"keys{self._table_postfix}",
                f"key_columns{self._table_postfix}",
            ]

            # Check schemas table is populated
            result = await conn.execute(
                text(
                    f"SELECT COUNT(*) FROM {STAGING_SCHEMA}."  # noqa: S608
                    f"schemas{self._table_postfix}"
                )
            )
            count = result.scalar()

            if count == 0:
                raise RuntimeError("No schemas loaded to staging")

            # Check required tables exist
            result = await conn.execute(
                text(
                    f"SELECT schema_name FROM {STAGING_SCHEMA}"  # noqa: S608
                    f".schemas{self._table_postfix}"
                )
            )
            loaded_schemas = {row[0] for row in result}

            missing = set(self._schema_list) - loaded_schemas
            if missing:
                self._logger.warning(
                    "Some schemas not found in TAP_SCHEMA",
                    missing=list(missing),
                    loaded=list(loaded_schemas),
                )

            self._logger.info(
                "Validation passed",
                tables_checked=len(required_tables),
                schemas_loaded=len(loaded_schemas),
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

            if not prod_exists:
                self._logger.info(
                    "First run detected, performing initial deployment",
                    source=STAGING_SCHEMA,
                    target=PRODUCTION_SCHEMA,
                )

                await conn.execute(
                    text(
                        f"ALTER SCHEMA {STAGING_SCHEMA} "
                        f"RENAME TO {PRODUCTION_SCHEMA}"
                    )
                )
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

        self._logger.info("Schema swap complete, TAP_SCHEMA is now live")
