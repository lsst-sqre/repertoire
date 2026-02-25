"""Integration testS for the CLI."""

import asyncio
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
from safir.testing.data import Data
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.postgres import PostgresContainer

from repertoire.cli import main


def test_update_tap_schema_integration(
    data: Data,
    postgres_container: PostgresContainer,
    tmp_path: Path,
) -> None:
    tap_config_file = data.path("config/tap.yaml")
    event_loop = asyncio.new_event_loop()
    db_url = postgres_container.get_connection_url()
    async_db_url = db_url.replace(
        "postgresql+psycopg2://", "postgresql+asyncpg://"
    )

    async def setup() -> None:
        """Clean up any existing schemas."""
        engine = create_async_engine(async_db_url, echo=False)
        async with engine.begin() as conn:
            await conn.execute(
                text("DROP SCHEMA IF EXISTS tap_schema CASCADE")
            )
            await conn.execute(
                text("DROP SCHEMA IF EXISTS tap_schema_staging CASCADE")
            )
        await engine.dispose()

    event_loop.run_until_complete(setup())

    with patch(
        "repertoire.storage.tap_schema.TAPSchemaStorage.download_and_extract"
    ) as mock_dl:
        mock_yaml_dir = tmp_path / "mock_schemas"
        mock_yaml_dir.mkdir(exist_ok=True)

        test_schema = """
name: dp02_dc2
description: Test schema
"@id": "#dp02_dc2"
tables:
  - name: test_table
    "@id": "#test_table"
    description: Test table
    columns:
      - name: id
        "@id": "#test_table.id"
        datatype: int
        description: Test ID
        nullable: false
"""
        (mock_yaml_dir / "dp02_dc2.yaml").write_text(test_schema)
        mock_dl.return_value = mock_yaml_dir

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "update-tap-schema",
                "--config-path",
                str(tap_config_file),
                "--app",
                "tap",
                "--database-url",
                async_db_url,
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert "TAP_SCHEMA update completed successfully" in result.output

    async def verify() -> None:
        """Verify schema was created correctly."""
        engine = create_async_engine(async_db_url, echo=False)

        async with engine.begin() as conn:
            res = await conn.execute(
                text(
                    "SELECT COUNT(*) FROM tap_schema.schemas11 "
                    "WHERE schema_name LIKE '%dp02_dc2%'"
                )
            )
            count = res.scalar()
            assert count is not None
            assert count > 0, "No schemas found in tap_schema.schemas11"

            res = await conn.execute(
                text(
                    "SELECT COUNT(*) FROM tap_schema.schemas "
                    "WHERE schema_name LIKE '%dp02_dc2%'"
                )
            )
            count = res.scalar()
            assert count is not None
            assert count > 0, "No schemas found in tap_schema.schemas view"

            res = await conn.execute(
                text("SELECT version FROM tap_schema.version")
            )
            version = res.scalar()
            assert version == "w.2025.43", f"Wrong version: {version}"

        await engine.dispose()

    event_loop.run_until_complete(verify())
    event_loop.close()
