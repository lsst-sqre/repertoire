"""Build and cache the service discovery information."""

from typing import Annotated

from fastapi import Depends

from rubin.repertoire import Discovery, RepertoireBuilder

from ..config import Config
from .config import config_dependency

__all__ = ["DiscoveryDependency", "discovery_dependency"]


class DiscoveryDependency:
    """Build and cache the service discovery information.

    Currently, service discovery information is only calculated once during
    startup. In the future, this may become more complex by using dynamic
    registration.
    """

    def __init__(self) -> None:
        self._discovery: Discovery | None = None

    async def __call__(
        self, config: Annotated[Config, Depends(config_dependency)]
    ) -> Discovery:
        """Generate discovery information if needed and return it."""
        if not self._discovery:
            self._discovery = RepertoireBuilder(config).build()
        return self._discovery


discovery_dependency = DiscoveryDependency()
"""The dependency that will return the current service discovery data."""
