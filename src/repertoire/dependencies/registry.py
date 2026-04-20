"""Build and cache the OAI-PMH registry handler."""

from datetime import datetime
from typing import Annotated

from fastapi import Depends, Request
from safir.dependencies.logger import logger_dependency
from structlog import BoundLogger

from rubin.repertoire import Discovery

from ..config import Config
from ..registry.factory import ResourceRecordFactory
from ..registry.oai import OaiHandler
from .config import config_dependency
from .discovery import discovery_dependency

__all__ = ["OaiHandlerDependency", "oai_handler_dependency"]


class OaiHandlerDependency:
    """Build and cache the OAI-PMH registry handler.

    The OAI-PMH handler is built on the first request and depends on the
    service discovery data and the registry configuration.
    """

    def __init__(self) -> None:
        self._handler: OaiHandler | None = None
        self._startup_timestamp: datetime | None = None

    async def __call__(
        self,
        config: Annotated[Config, Depends(config_dependency)],
        discovery: Annotated[Discovery, Depends(discovery_dependency)],
        logger: Annotated[BoundLogger, Depends(logger_dependency)],
        request: Request,
    ) -> OaiHandler:
        """Return the cached OAI-PMH handler.

        Parameters
        ----------
        config
            Full Repertoire configuration.
        discovery
            Pre-rendered service discovery data with resolved URLs.
        request
            Incoming HTTP request, used to derive the absolute URL.

        Returns
        -------
        OaiHandler
            The shared handler instance for this application lifetime.

        Raises
        ------
        RuntimeError
            If `initialize` has not been called.
        """
        if self._startup_timestamp is None:
            raise RuntimeError(
                "OaiHandlerDependency.initialize() must be "
                "called from the application lifespan before "
                "any requests are processed"
            )
        if self._handler is None:
            if config.registry is None:
                raise RuntimeError(
                    "OAI handler dependency called without registry"
                    " configuration"
                )
            oai_url = str(request.url_for("get_oai"))
            store = ResourceRecordFactory(
                config=config,
                discovery=discovery,
                startup_timestamp=self._startup_timestamp,
                oai_url=oai_url,
                logger=logger,
            ).create_all()

            # Initialize the handler for the first request and cache it.
            # Ideally this would be done at application startup, but the
            # handler needs the absolute OAI endpoint URL, which would have
            # to then be constructed from configuration.
            self._handler = OaiHandler(store, oai_url, config.registry)
        return self._handler

    def initialize(self, startup_timestamp: datetime) -> None:
        """Initialize the OAI-PMH handler dependency.

        Must be called from the application lifespan before any requests are
        processed.

        Parameters
        ----------
        startup_timestamp
            Timestamp captured at application startup, stamped as the
            ``updated`` datestamp on all VOResource records.
        """
        # The timestamp is passed to the factory and then to the handler,
        # and ends up being used as the `updated` datestamp on all records.
        self._startup_timestamp = startup_timestamp
        self._handler = None


oai_handler_dependency = OaiHandlerDependency()
"""The dependency that will return the OAI-PMH registry handler."""
