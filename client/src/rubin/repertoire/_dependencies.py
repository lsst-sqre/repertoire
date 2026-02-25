"""FastAPI dependencies providing service discovery information."""

from typing import Annotated

from fastapi import Depends
from httpx import AsyncClient
from safir.dependencies.http_client import http_client_dependency
from structlog.stdlib import BoundLogger

from ._client import DiscoveryClient

__all__ = ["DiscoveryDependency", "discovery_dependency"]


class DiscoveryDependency:
    """Maintain a global Repertoire client for service discovery.

    This is structured as a dependency that creates and caches the client on
    first use to delay client creation until runtime so that the test suite
    has a chance to initialize environment variables.
    """

    def __init__(self) -> None:
        self._http_client: AsyncClient | None = None
        self._client: DiscoveryClient | None = None
        self._logger: BoundLogger | None = None

    async def __call__(
        self,
        http_client: Annotated[AsyncClient, Depends(http_client_dependency)],
    ) -> DiscoveryClient:
        if not self._client or self._http_client != http_client:
            self._client = DiscoveryClient(http_client, logger=self._logger)
            self._http_client = http_client
        return self._client

    def initialize(self, logger: BoundLogger) -> None:
        """Set the logger to use for service discovery."""
        self._logger = logger


discovery_dependency = DiscoveryDependency()
"""The cached Repertoire client as a FastAPI dependency."""
