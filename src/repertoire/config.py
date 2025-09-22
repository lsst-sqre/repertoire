"""Configuration definition."""

from __future__ import annotations

from pydantic import AliasChoices, Field, SecretStr
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

    log_profile: Profile = Field(
        Profile.development, title="Application logging profile"
    )

    name: str = Field("Repertoire", title="Name of application")

    path_prefix: str = Field("/repertoire", title="URL prefix for application")

    slack_alerts: bool = Field(
        False,
        title="Enable Slack alerts",
        description="If true, slackWebhook must also be set",
    )

    slack_webhook: SecretStr | None = Field(
        None,
        title="Slack webhook for alerts",
        description="If set, alerts will be posted to this Slack webhook",
        validation_alias=AliasChoices(
            "REPERTOIRE_SLACK_WEBHOOK", "slackWebhook"
        ),
    )

    token: SecretStr | None = Field(
        None,
        title="Gafaelfawr token",
        description="Gafaelfawr token for HiPS property file retrieval",
        validation_alias=AliasChoices("REPERTOIRE_TOKEN", "token"),
    )

    def configure_logging(self) -> None:
        """Configure logging based on the Repertoire configuration."""
        configure_logging(
            profile=self.log_profile,
            log_level=self.log_level,
            name="repertoire",
        )
        if self.log_profile == Profile.production:
            configure_uvicorn_logging(self.log_level)
