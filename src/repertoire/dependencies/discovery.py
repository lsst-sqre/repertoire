"""Build and cache the service discovery information."""

from typing import Annotated

from fastapi import Depends, Request

from rubin.repertoire import Discovery, RepertoireBuilder

from .builder import builder_dependency

__all__ = ["DiscoveryDependency", "discovery_dependency"]


class DiscoveryDependency:
    """Build and cache the service discovery information.

    Currently, service discovery information is only calculated once during
    startup. In the future, this may become more complex by using dynamic
    registration.
    """

    def __init__(self) -> None:
        self._discovery: Discovery | None = None
        self._old_builder: RepertoireBuilder | None = None

    async def __call__(
        self,
        builder: Annotated[RepertoireBuilder, Depends(builder_dependency)],
        request: Request,
    ) -> Discovery:
        """Generate discovery information if needed and return it."""
        if not self._discovery or builder != self._old_builder:
            base_url = request.url_for("get_root")
            self._discovery = builder.build_discovery(str(base_url))
            self._old_builder = builder
        return self._discovery


discovery_dependency = DiscoveryDependency()
"""The dependency that will return the current service discovery data."""
