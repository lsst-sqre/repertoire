"""Cache the Repertoire builder."""

from pathlib import Path
from typing import Annotated

from fastapi import Depends

from rubin.repertoire import RepertoireBuilderWithSecrets

from ..config import Config
from .config import config_dependency

__all__ = ["BuilderDependency", "builder_dependency"]


class BuilderDependency:
    """Construct and cache the Repertoire builder."""

    def __init__(self) -> None:
        self._secrets_root: str | Path | None = None
        self._builder: RepertoireBuilderWithSecrets | None = None
        self._old_config: Config | None = None

    async def __call__(
        self,
        config: Annotated[Config, Depends(config_dependency)],
    ) -> RepertoireBuilderWithSecrets:
        """Return the cached Repertoire builder."""
        if self._secrets_root is None:
            raise AssertionError("Builder dependency not initialized")
        if not self._builder or config != self._old_config:
            secrets = self._secrets_root
            self._builder = RepertoireBuilderWithSecrets(config, secrets)
            self._old_config = config
        return self._builder

    def initialize(self, secrets_root: str | Path) -> None:
        """Create the Repertoire builder.

        Parameters
        ----------
        secrets_root
            Root path to the mounted Repertoire secret.
        """
        self._secrets_root = secrets_root


builder_dependency = BuilderDependency()
"""The dependency that will return the Repertoire builder."""
