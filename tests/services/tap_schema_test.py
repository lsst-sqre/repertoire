"""Tests for TAP schema database operations."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from structlog.stdlib import BoundLogger

from repertoire.exceptions import (
    TAPSchemaNotFoundError,
    TAPSchemaValidationError,
)
from repertoire.services.tap_schema import TAPSchemaService
from repertoire.storage.tap_schema import TAPSchemaStorage


@pytest.fixture
def storage(logger: BoundLogger) -> TAPSchemaStorage:
    """Provide a test storage instance."""
    return TAPSchemaStorage(logger)


@pytest.mark.asyncio
async def test_initialize_schemas(
    engine: AsyncEngine,
    logger: BoundLogger,
    database_password: str,
) -> None:
    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["dp02_dc2"],
        source_url_template="https://example.com/{version}.tar.gz",
        database_password=database_password,
    )
    await service._initialize_schemas()

    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name LIKE 'tap_schema_staging'"
            )
        )
        schemas = [row[0] for row in result]
        assert "tap_schema_staging" in schemas


@pytest.mark.asyncio
async def test_create_views(
    engine: AsyncEngine,
    logger: BoundLogger,
    database_password: str,
) -> None:
    """Test view creation."""
    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["dp02_dc2"],
        source_url_template="https://example.com/{version}.tar.gz",
        database_password=database_password,
    )

    async with engine.begin() as conn:
        await conn.execute(
            text("CREATE SCHEMA IF NOT EXISTS tap_schema_staging")
        )

        for table in [
            "schemas11",
            "tables11",
            "columns11",
            "keys11",
            "key_columns11",
            "version",
        ]:
            await conn.execute(
                text(
                    f"CREATE TABLE IF NOT EXISTS tap_schema_staging.{table} "
                    f"(id INT)"
                )
            )

    await service._create_views()

    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.views "
                "WHERE table_schema='tap_schema_staging'"
            )
        )
        views = {row[0] for row in result}
        expected_views = {
            "schemas",
            "tables",
            "columns",
            "keys",
            "key_columns",
        }
        assert expected_views.issubset(views)


@pytest.mark.asyncio
async def test_record_version(
    engine: AsyncEngine,
    logger: BoundLogger,
    database_password: str,
) -> None:
    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["dp02_dc2"],
        source_url_template="https://example.com/{version}.tar.gz",
        database_password=database_password,
    )

    async with engine.begin() as conn:
        await conn.execute(
            text("CREATE SCHEMA IF NOT EXISTS tap_schema_staging")
        )

    await service._record_version()

    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT version FROM tap_schema_staging.version")
        )
        version = result.scalar()
        assert version == "w.2025.43"


@pytest.mark.asyncio
async def test_swap_schemas(
    engine: AsyncEngine,
    logger: BoundLogger,
    database_password: str,
) -> None:
    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["dp02_dc2"],
        source_url_template="https://example.com/{version}.tar.gz",
        database_password=database_password,
    )

    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS tap_schema CASCADE"))
        await conn.execute(
            text("DROP SCHEMA IF EXISTS tap_schema_staging CASCADE")
        )
        await conn.execute(text("CREATE SCHEMA tap_schema"))
        await conn.execute(text("CREATE SCHEMA tap_schema_staging"))
        await conn.execute(text("CREATE TABLE tap_schema.test (id INT)"))
        await conn.execute(
            text("CREATE TABLE tap_schema_staging.test (id INT, name TEXT)")
        )

    await service._swap_schemas()

    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'tap_schema' "
                "AND table_name = 'test' "
                "ORDER BY column_name"
            )
        )
        columns = [row[0] for row in result]
        assert columns == ["id", "name"]


@pytest.mark.asyncio
async def test_validate_staging_success(
    engine: AsyncEngine,
    logger: BoundLogger,
    database_password: str,
) -> None:
    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["dp02_dc2"],
        source_url_template="https://example.com/{version}.tar.gz",
        database_password=database_password,
    )

    async with engine.begin() as conn:
        await conn.execute(
            text("CREATE SCHEMA IF NOT EXISTS tap_schema_staging")
        )
        await conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS tap_schema_staging.schemas11 "
                "(schema_name TEXT)"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO tap_schema_staging.schemas11 VALUES ('dp02_dc2')"
            )
        )

    await service._validate_staging()


@pytest.mark.asyncio
async def test_validate_staging_failure(
    engine: AsyncEngine,
    logger: BoundLogger,
    database_password: str,
) -> None:
    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["dp02_dc2"],
        source_url_template="https://example.com/{version}.tar.gz",
        database_password=database_password,
    )

    async with engine.begin() as conn:
        await conn.execute(
            text("CREATE SCHEMA IF NOT EXISTS tap_schema_staging")
        )
        await conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS tap_schema_staging.schemas11 "
                "(schema_name TEXT)"
            )
        )

    with pytest.raises(
        TAPSchemaValidationError, match="Expected 1 schemas but found 0"
    ):
        await service._validate_staging()


@pytest.mark.asyncio
async def test_service_workflow_orchestration(
    engine: AsyncEngine,
    logger: BoundLogger,
    tmp_path: Path,
    database_url: str,
) -> None:
    mock_yaml_dir = tmp_path / "schemas"
    mock_yaml_dir.mkdir()

    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["test_schema"],
        source_url_template="https://example.com/{version}.tar.gz",
    )

    sync_url = database_url.replace(
        "postgresql+asyncpg://", "postgresql+psycopg2://"
    )

    with (
        patch.object(
            service._storage, "download_and_extract"
        ) as mock_download,
        patch.object(service, "_initialize_schemas") as mock_init_schemas,
        patch.object(service, "_create_sync_url") as mock_create_url,
        patch.object(service, "_create_table_manager") as mock_create_mgr,
        patch.object(service, "_initialize_database") as mock_init_db,
        patch.object(service, "_load_schemas") as mock_load,
        patch.object(service, "_record_version") as mock_version,
        patch.object(service, "_create_views") as mock_views,
        patch.object(service, "_validate_staging") as mock_validate,
        patch.object(service, "_swap_schemas") as mock_swap,
    ):
        mock_download.return_value = mock_yaml_dir
        mock_create_url.return_value = sync_url
        mock_create_mgr.return_value = MagicMock()

        await service.update(tmp_path)

        mock_init_schemas.assert_called_once()
        mock_create_url.assert_called_once()
        mock_create_mgr.assert_called_once()
        mock_init_db.assert_called_once()
        mock_download.assert_called_once()
        mock_load.assert_called_once()
        mock_version.assert_called_once()
        mock_views.assert_called_once()
        mock_validate.assert_called_once()
        mock_swap.assert_called_once()


@pytest.mark.asyncio
async def test_service_cleanup_on_error(
    engine: AsyncEngine,
    logger: BoundLogger,
    tmp_path: Path,
    database_url: str,
) -> None:
    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["test_schema"],
        source_url_template="https://example.com/{version}.tar.gz",
    )

    sync_url = database_url.replace(
        "postgresql+asyncpg://", "postgresql+psycopg2://"
    )

    with (
        patch.object(
            service._storage, "download_and_extract"
        ) as mock_download,
        patch.object(service, "_create_sync_url") as mock_create_url,
        patch.object(service, "_create_table_manager") as mock_create_mgr,
        patch.object(service, "_load_schemas") as mock_load,
    ):
        mock_download.return_value = tmp_path
        mock_create_url.return_value = sync_url
        mock_create_mgr.return_value = MagicMock()

        mock_load.side_effect = RuntimeError("Load failed")

        with pytest.raises(RuntimeError, match="Load failed"):
            await service.update(tmp_path)


@pytest.mark.asyncio
async def test_service_handles_missing_schema_file(
    engine: AsyncEngine,
    logger: BoundLogger,
    tmp_path: Path,
    database_url: str,
) -> None:
    mock_yaml_dir = tmp_path / "schemas"
    mock_yaml_dir.mkdir()

    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["nonexistent_schema"],
        source_url_template="https://example.com/{version}.tar.gz",
    )

    sync_url = database_url.replace(
        "postgresql+asyncpg://", "postgresql+psycopg2://"
    )

    with (
        patch.object(
            service._storage, "download_and_extract"
        ) as mock_download,
        patch.object(service, "_initialize_schemas") as mock_init_schemas,
        patch.object(service, "_create_sync_url") as mock_create_url,
        patch.object(service, "_create_table_manager") as mock_create_mgr,
        patch.object(service, "_initialize_database") as mock_init_db,
    ):
        mock_download.return_value = mock_yaml_dir
        mock_create_url.return_value = sync_url

        mock_mgr = MagicMock()
        mock_create_mgr.return_value = mock_mgr

        with pytest.raises(TAPSchemaNotFoundError, match="Schema not found"):
            await service.update(tmp_path)

        mock_init_schemas.assert_called_once()
        mock_create_url.assert_called_once()
        mock_create_mgr.assert_called_once()
        mock_init_db.assert_called_once()
        mock_download.assert_called_once()


@pytest.mark.asyncio
async def test_initialize_schemas_first_run(
    engine: AsyncEngine,
    logger: BoundLogger,
) -> None:
    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["dp02_dc2"],
        source_url_template="https://example.com/{version}.tar.gz",
    )

    await service._initialize_schemas()

    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name LIKE 'tap_schema_staging'"
            )
        )
        schemas = [row[0] for row in result]
        assert "tap_schema_staging" in schemas


@pytest.mark.asyncio
async def test_initialize_schemas_subsequent_run(
    engine: AsyncEngine,
    logger: BoundLogger,
) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA tap_schema"))
        await conn.execute(
            text("CREATE TABLE tap_schema.test_table (id INT, data TEXT)")
        )
        await conn.execute(
            text("INSERT INTO tap_schema.test_table VALUES (1, 'preserved')")
        )

    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["dp02_dc2"],
        source_url_template="https://example.com/{version}.tar.gz",
    )

    await service._initialize_schemas()

    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name IN ('tap_schema', 'tap_schema_staging')"
            )
        )
        schemas = [row[0] for row in result]
        assert "tap_schema" in schemas
        assert "tap_schema_staging" in schemas

        result = await conn.execute(
            text("SELECT data FROM tap_schema.test_table WHERE id = 1")
        )
        data = result.scalar()
        assert data == "preserved"


@pytest.mark.asyncio
async def test_swap_schemas_first_run(
    engine: AsyncEngine,
    logger: BoundLogger,
) -> None:
    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["dp02_dc2"],
        source_url_template="https://example.com/{version}.tar.gz",
    )

    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA tap_schema_staging"))
        await conn.execute(
            text("CREATE TABLE tap_schema_staging.test (id INT, data TEXT)")
        )
        await conn.execute(
            text("INSERT INTO tap_schema_staging.test VALUES (1, 'new')")
        )

    await service._swap_schemas()

    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name = 'tap_schema'"
            )
        )
        assert result.scalar() == "tap_schema"

        result = await conn.execute(
            text("SELECT data FROM tap_schema.test WHERE id = 1")
        )
        assert result.scalar() == "new"

        result = await conn.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name = 'tap_schema_staging'"
            )
        )
        assert result.scalar() is None


@pytest.mark.asyncio
async def test_swap_schemas_subsequent_run(
    engine: AsyncEngine,
    logger: BoundLogger,
) -> None:
    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["dp02_dc2"],
        source_url_template="https://example.com/{version}.tar.gz",
    )

    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA tap_schema"))
        await conn.execute(
            text("CREATE TABLE tap_schema.test (id INT, data TEXT)")
        )
        await conn.execute(
            text("INSERT INTO tap_schema.test VALUES (1, 'old')")
        )

        await conn.execute(text("CREATE SCHEMA tap_schema_staging"))
        await conn.execute(
            text("CREATE TABLE tap_schema_staging.test (id INT, data TEXT)")
        )
        await conn.execute(
            text("INSERT INTO tap_schema_staging.test VALUES (1, 'new')")
        )

    await service._swap_schemas()

    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT data FROM tap_schema.test WHERE id = 1")
        )
        assert result.scalar() == "new"

        result = await conn.execute(
            text("SELECT data FROM tap_schema_staging.test WHERE id = 1")
        )
        assert result.scalar() == "old"


@pytest.mark.asyncio
async def test_validate_staging_with_multiple_schemas(
    engine: AsyncEngine,
    logger: BoundLogger,
) -> None:
    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["dp02_dc2", "ivoa_obscore"],
        source_url_template="https://example.com/{version}.tar.gz",
    )

    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA tap_schema_staging"))
        await conn.execute(
            text(
                "CREATE TABLE tap_schema_staging.schemas11 "
                "(schema_name TEXT, description TEXT)"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO tap_schema_staging.schemas11 VALUES "
                "('dp02_dc2', 'Data Preview 0.2'), "
                "('ivoa_obscore', 'IVOA ObsCore')"
            )
        )

    await service._validate_staging()


@pytest.mark.asyncio
async def test_record_version_creates_table(
    engine: AsyncEngine,
    logger: BoundLogger,
) -> None:
    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["dp02_dc2"],
        source_url_template="https://example.com/{version}.tar.gz",
    )

    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA tap_schema_staging"))

    await service._record_version()

    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT version FROM tap_schema_staging.version "
                "WHERE version = :ver"
            ),
            {"ver": "w.2025.43"},
        )
        version = result.scalar()
        assert version == "w.2025.43"


@pytest.mark.asyncio
async def test_record_version_updates_existing(
    engine: AsyncEngine,
    logger: BoundLogger,
) -> None:
    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["dp02_dc2"],
        source_url_template="https://example.com/{version}.tar.gz",
    )

    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA tap_schema_staging"))

    await service._record_version()

    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT loaded_at FROM tap_schema_staging.version "
                "WHERE version = :ver"
            ),
            {"ver": "w.2025.43"},
        )
        first_timestamp = result.scalar()

    await asyncio.sleep(0.1)

    await service._record_version()

    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT loaded_at FROM tap_schema_staging.version "
                "WHERE version = :ver"
            ),
            {"ver": "w.2025.43"},
        )
        second_timestamp = result.scalar()

    if first_timestamp is None or second_timestamp is None:
        pytest.fail("Timestamps should not be None")

    assert second_timestamp > first_timestamp


@pytest.mark.asyncio
async def test_create_views_accessible(
    engine: AsyncEngine,
    logger: BoundLogger,
) -> None:
    service = TAPSchemaService(
        engine=engine,
        logger=logger,
        storage=TAPSchemaStorage(logger),
        schema_version="w.2025.43",
        schema_list=["dp02_dc2"],
        source_url_template="https://example.com/{version}.tar.gz",
    )

    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA tap_schema_staging"))

        for table in [
            "schemas11",
            "tables11",
            "columns11",
            "keys11",
            "key_columns11",
            "version",
        ]:
            await conn.execute(
                text(
                    f"CREATE TABLE tap_schema_staging.{table} "
                    f"(id INT, name TEXT)"
                )
            )
            await conn.execute(
                text(
                    f"INSERT INTO tap_schema_staging.{table} "  # noqa: S608
                    f"VALUES (1, 'test_{table}')"
                )
            )

    await service._create_views()

    async with engine.begin() as conn:
        for view in ["schemas", "tables", "columns"]:
            result = await conn.execute(
                text(
                    f"SELECT name FROM tap_schema_staging.{view} WHERE id = 1"  # noqa: S608
                )
            )
            name = result.scalar()
            assert name == f"test_{view}11"
