"""Configuration model for Repertoire."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from pydantic.alias_generators import to_camel
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    "DatasetConfig",
    "RepertoireSettings",
    "Rule",
]


class DatasetConfig(BaseModel):
    """Metadata for an available dataset."""

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    name: Annotated[
        str,
        Field(
            title="Name",
            description="Human-readable name of the dataset",
        ),
    ]


class BaseRule(BaseModel):
    """Base class for rules for deriving URLs."""

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    type: Annotated[str, Field(title="Type of service")]

    name: Annotated[
        str,
        Field(
            title="Service name",
            description="Name of service discovery service",
        ),
    ]

    template: Annotated[
        str,
        Field(
            title="Template", description="Jinja template to generate the URL"
        ),
    ]


class DataServiceRule(BaseRule):
    """Rule for a Phalanx service associated with a dataset."""

    type: Annotated[Literal["data"], Field(title="Type of service")]

    datasets: Annotated[
        list[str] | None,
        Field(
            title="Applicable datasets",
            description=(
                "Datasets served by this service. If not given, defaults to"
                " all available datasets."
            ),
        ),
    ] = None


class InternalServiceRule(BaseRule):
    """Rule for an internal Phalanx service not associated with a dataset."""

    type: Annotated[Literal["internal"], Field(title="Type of service")]


class UiServiceRule(BaseRule):
    """Rule for a UI Phalanx service accessed via a web browser."""

    type: Annotated[Literal["ui"], Field(title="Type of service")]


type Rule = Annotated[
    DataServiceRule | InternalServiceRule | UiServiceRule,
    Field(discriminator="type"),
]


class RepertoireSettings(BaseSettings):
    """Base configuration from which Repertoire constructs URLs.

    This roughly represents the merged Phalanx configuration of the Repertoire
    service for a given environment, and is also used during the Phalanx build
    process to build static service discovery information. It is defined with
    ``pydantic_settings.BaseSettings`` as the base class instead of
    ``pydantic.BaseModel`` so that the main settings class of the Repertoire
    server can inherit from it.
    """

    model_config = SettingsConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    applications: Annotated[
        set[str],
        Field(
            title="Phalanx applications",
            description="Names of deployed Phalanx applications",
        ),
    ] = set()

    base_hostname: Annotated[
        str,
        Field(
            title="Base hostname",
            description="Base hostname for the Phalanx environment",
        ),
    ]

    butler_configs: Annotated[
        dict[str, HttpUrl],
        Field(
            title="Butler config URLs",
            description="Mapping of dataset names to Butler config URLs",
        ),
    ] = {}

    datasets: Annotated[
        list[DatasetConfig],
        Field(
            title="Datasets",
            description="Metadata about available datasets",
        ),
    ] = []

    rules: Annotated[
        dict[str, list[Rule]],
        Field(
            title="Phalanx service rules",
            description=(
                "Rules mapping Phalanx service names to instructions for what"
                " to include in service discovery for that service. These"
                " rules are used if the service is not running on a subdomain."
            ),
        ),
    ] = {}

    subdomain_rules: Annotated[
        dict[str, list[Rule]],
        Field(
            title="Phalanx subdomain service rules",
            description=(
                "Rules mapping Phalanx service names to instructions for what"
                " to include in service discovery for that service. These"
                " rules are used if the service is running on a subdomain."
            ),
        ),
    ] = {}

    use_subdomains: Annotated[
        set[str],
        Field(
            title="Services using subdomains",
            description=(
                "List of Phalanx services deployed to a subdomain. These"
                " services use the subdomain rules instead of the regular"
                " rules."
            ),
        ),
    ] = set()

    @classmethod
    def from_file(cls, path: Path) -> Self:
        """Construct the configuration from a YAML file.

        Parameters
        ----------
        path
            Path to the configuration file in YAML.

        Returns
        -------
        RepertoireSettings
            The corresponding configuration.
        """
        with path.open("r") as f:
            return cls.model_validate(yaml.safe_load(f))
