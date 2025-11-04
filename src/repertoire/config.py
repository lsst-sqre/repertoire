"""Configuration definition."""

from __future__ import annotations

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic.alias_generators import to_camel
from safir.logging import (
    LogLevel,
    Profile,
    configure_logging,
    configure_uvicorn_logging,
)
from safir.metrics import MetricsConfiguration, metrics_configuration_factory

from rubin.repertoire import RepertoireSettings

__all__ = ["Config"]


class SentryConfig(BaseModel):
    """Sentry configuration for Repertoire.

    This configuration is not used internally, but has to be present in the
    model so that we can forbid unknown configuration settings. Otherwise,
    Phalanx wouldn't be able to use the full ``config`` key of the Helm values
    as the configuration file.
    """

    enabled: bool = Field(False, title="Whether to send exceptions to Sentry")


class TapServerConfig(BaseModel):
    """Configuration for a TAP server."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        populate_by_name=True,
    )

    enabled: bool = Field(
        True,
        title="Enable TAP schema management for this server",
        description=(
            "Controls whether repertoire manages TAP_SCHEMA for this server. "
            "Set to false in environments where this TAP server doesn't exist "
            "or doesn't use CloudSQL."
        ),
    )

    schema_version: str | None = Field(
        None,
        title="Schema version override for this server",
        description=(
            "Override the global schemaVersion for this specific server. "
            "If not set, uses config.schemaVersion."
        ),
    )

    schemas: list[str] = Field(
        ...,
        title="List of schema names to load",
        description="Schema YAML file names (without .yaml extension)",
    )

    database: str = Field(
        ...,
        title="Database name",
        description="Database name for this TAP server",
    )

    database_user: str = Field(
        ...,
        title="Database username",
        description="Username for this TAP server",
    )

    database_password_key: str = Field(
        ...,
        title="Secret key for database password",
        description="Key in repertoire secret containing the server password",
    )

    @field_validator("schemas")
    @classmethod
    def schemas_not_empty(cls, v: list[str]) -> list[str]:
        """Ensure schemas list is not empty."""
        if not v:
            raise ValueError("schemas list cannot be empty")
        return v


class Config(RepertoireSettings):
    """Configuration for Repertoire."""

    log_level: LogLevel = Field(
        LogLevel.INFO, title="Log level of the application's logger"
    )

    log_profile: Profile = Field(
        Profile.development, title="Application logging profile"
    )

    metrics: MetricsConfiguration = Field(
        default_factory=metrics_configuration_factory,
        title="Metrics configuration",
    )

    name: str = Field("Repertoire", title="Name of application")

    path_prefix: str = Field("/repertoire", title="URL prefix for application")

    sentry: SentryConfig | None = Field(None, title="Sentry configuration")

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

    schema_version: str | None = Field(
        None,
        title="Default schema version",
        description="Schema version to use",
    )

    schema_source_template: str | None = Field(
        None,
        title="URL template for schema downloads",
        description=(
            "Template for schema download URLs."
            "Examples: 'gs://bucket/{version}.tar.gz'"
        ),
    )

    tap_servers: dict[str, TapServerConfig] = Field(
        default_factory=dict,
        title="TAP schema configuration by application",
        description=(
            "Configuration for TAP servers whose TAP_SCHEMA tables are "
            "managed by repertoire. Keys are application names "
            "(tap, ssotap, etc)."
        ),
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

    def get_tap_server_schema_version(self, server_name: str) -> str:
        """Get the schema version for a TAP server.

        Parameters
        ----------
        server_name
            Name of the TAP server.

        Returns
        -------
        str
            The schema version to use (server-specific or global default).

        Raises
        ------
        ValueError
            If no schema version is configured at either level.
        """
        server_config = self.tap_servers.get(server_name)
        if not server_config:
            raise ValueError(f"Unknown TAP server: {server_name}")

        version = server_config.schema_version or self.schema_version

        if not version:
            raise ValueError(
                f"No schema version configured for server '{server_name}'. "
                f"Set either config.schemaVersion or "
                f"config.tapServers.{server_name}.schemaVersion"
            )

        return version

    @model_validator(mode="after")
    def validate_tap_servers(self) -> Config:
        """Validate TAP server config consistency.

        Returns
        -------
        Config
            The validated configuration.

        Raises
        ------
        ValueError
            If any enabled TAP server is missing required settings.
        """
        if not self.tap_servers:
            return self

        enabled_servers = [
            name for name, cfg in self.tap_servers.items() if cfg.enabled
        ]

        if not enabled_servers:
            return self

        if not self.schema_source_template:
            raise ValueError(
                "schema_source_template must be set when tap_servers "
                "has enabled servers"
            )

        # Check each server has a version
        for server_name in enabled_servers:
            server_config = self.tap_servers[server_name]
            if not server_config.schema_version and not self.schema_version:
                raise ValueError(
                    f"No schema version configured for enabled server "
                    f"'{server_name}'. "
                    f"Set either config.schemaVersion or "
                    f"config.tapServers.{server_name}.schemaVersion"
                )

        return self
