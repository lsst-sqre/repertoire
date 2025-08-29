"""Configuration definition."""

from __future__ import annotations

from pydantic import Field, SecretStr
from safir.logging import (
    LogLevel,
    Profile,
    configure_logging,
    configure_uvicorn_logging,
)

from rubin.repertoire import RepertoireSettings

__all__ = ["Config"]


class Config(RepertoireSettings):
    """Configuration for Repertoire."""

    log_level: LogLevel = Field(
        LogLevel.INFO, title="Log level of the application's logger"
    )

    name: str = Field("Repertoire", title="Name of application")

    path_prefix: str = Field("/repertoire", title="URL prefix for application")

    profile: Profile = Field(
        Profile.development, title="Application logging profile"
    )

    slack_webhook: SecretStr | None = Field(
        None,
        title="Slack webhook for alerts",
        description="If set, alerts will be posted to this Slack webhook",
    )

    def configure_logging(self) -> None:
        """Configure logging based on the Repertoire configuration."""
        configure_logging(
            profile=self.profile, log_level=self.log_level, name="repertoire"
        )
        if self.profile == Profile.production:
            configure_uvicorn_logging(self.log_level)
