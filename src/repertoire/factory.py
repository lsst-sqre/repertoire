"""Factory for creating Repertoire service and storage objects."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncEngine

from repertoire.config import Config
from repertoire.services.tap_schema import TAPSchemaService
from repertoire.storage.tap_schema import TAPSchemaStorage

if TYPE_CHECKING:
    from structlog.stdlib import BoundLogger

__all__ = ["Factory"]


class Factory:
    """Build Repertoire components.

    Parameters
    ----------
    config
        Repertoire configuration.
    engine
        Async SQLAlchemy engine for database operations.
    logger
        Logger for error messages and debugging.
    """

    def __init__(
        self,
        config: Config,
        engine: AsyncEngine,
        logger: BoundLogger,
    ) -> None:
        self._config = config
        self._engine = engine
        self._logger = logger

    def create_schema_storage(self) -> TAPSchemaStorage:
        """Create a schema storage instance.

        Returns
        -------
        TAPSchemaStorage
            Storage layer for schema download and extraction operations.
        """
        return TAPSchemaStorage(self._logger)

    def create_tap_schema_service(
        self,
        *,
        app: str,
        database_password: str | None = None,
    ) -> TAPSchemaService:
        """Create a TAP schema management service instance.

        Parameters
        ----------
        app
            TAP application name (tap, ssotap, etc.).
        database_password
            Password for the database user, if needed.

        Returns
        -------
        TAPSchemaService
            Fully configured TAP schema service.

        Raises
        ------
        ValueError
            If the app is not configured or schema version cannot be resolved.
        """
        schema_version = self._config.get_tap_server_schema_version(app)
        server_config = self._config.tap_servers[app]
        storage = self.create_schema_storage()

        return TAPSchemaService(
            engine=self._engine,
            logger=self._logger,
            storage=storage,
            schema_version=schema_version,
            schema_list=server_config.schemas,
            source_url_template=self._config.schema_source_template or "",
            database_password=database_password,
            table_postfix="11",
            extensions_path=self._config.tap_schema_extensions_path,
        )
