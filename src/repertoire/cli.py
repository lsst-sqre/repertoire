"""Command-line interface for Repertoire."""

from __future__ import annotations

import os
from pathlib import Path

import click
import structlog
from safir.asyncio import run_with_asyncio
from safir.database import create_database_engine
from sqlalchemy.engine.url import make_url

from repertoire.dependencies.config import config_dependency
from repertoire.tap_schema.manager import TapSchemaManager

__all__ = ["main"]


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(message="%(version)s")
def main() -> None:
    """Administrative command-line interface for Repertoire."""


@main.command("update-tap-schema")
@click.option(
    "--config-path",
    envvar="REPERTOIRE_CONFIG_PATH",
    type=click.Path(path_type=Path),
    default=None,
    help="Application configuration file.",
)
@click.option(
    "--app",
    envvar="REPERTOIRE_TAP_APP",
    required=True,
    help="TAP application name (tap, ssotap, etc.)",
)
@click.option(
    "--database-url",
    envvar="REPERTOIRE_DATABASE_URL",
    default=None,
    help="Override database URL (for testing)",
)
@run_with_asyncio
async def update_tap_schema_command(
    *,
    config_path: Path | None,
    app: str,
    database_url: str | None = None,
) -> None:
    """Update TAP_SCHEMA for a TAP application.

    This handles the complete workflow: initialize tables if needed,
    load schemas to staging, validate and swap to live.

    Examples
    --------
    Update TAP schema for the 'tap' server::

        $ repertoire update-tap-schema --app tap
    """
    if config_path:
        config_dependency.set_config_path(config_path)
    config = config_dependency.config()
    logger = structlog.get_logger("repertoire")

    try:
        schema_version = config.get_tap_server_schema_version(app)
    except ValueError as e:
        raise click.ClickException(str(e)) from e

    server_config = config.tap_servers[app]

    logger.info(
        "Starting TAP schema update",
        app=app,
        version=schema_version,
        schemas=server_config.schemas,
        database=server_config.database,
        database_user=server_config.database_user,
    )

    db_password_env = os.getenv("REPERTOIRE_DATABASE_PASSWORD")
    db_user_env = os.getenv("REPERTOIRE_DATABASE_USER")

    if database_url:
        url_parts = make_url(database_url)
        db_password = url_parts.password or db_password_env
    else:
        db_user = db_user_env or server_config.database_user
        db_password = db_password_env

        if not db_password:
            raise click.ClickException(
                f"Database password not found for TAP server: {app}\n"
                f"Set REPERTOIRE_DATABASE_PASSWORD environment variable"
            )

        database_url = (
            f"postgresql://{db_user}@127.0.0.1:5432/{server_config.database}"
        )

    engine = create_database_engine(database_url, db_password)

    try:
        manager = TapSchemaManager(
            engine=engine,
            logger=logger,
            schema_version=schema_version,
            schema_list=server_config.schemas,
            source_url_template=config.schema_source_template
            or "",  # Satisfy mypy
            database_password=db_password,
        )
        await manager.update()

        logger.info(
            "TAP_SCHEMA update completed successfully",
            app=app,
            version=schema_version,
            schema_count=len(server_config.schemas),
        )
    except Exception as e:
        logger.exception(
            "TAP_SCHEMA update failed",
            app=app,
            error=str(e),
        )
        raise click.ClickException(f"Update failed: {e}") from e
    finally:
        await engine.dispose()
