"""Configuration model for Repertoire."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from pydantic.alias_generators import to_camel
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    "ApiVersionRule",
    "BaseRule",
    "DataServiceRule",
    "DatasetConfig",
    "HipsConfig",
    "HipsDatasetConfig",
    "HipsLegacyConfig",
    "InfluxDatabaseConfig",
    "InternalServiceRule",
    "RepertoireSettings",
    "Rule",
    "UiServiceRule",
    "VersionedServiceRule",
]


class DatasetConfig(BaseModel):
    """Metadata for an available dataset."""

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    description: Annotated[
        str,
        Field(
            title="Description", description="Long description of the dataset"
        ),
    ]


class HipsDatasetConfig(BaseModel):
    """Configuration for a single HiPS dataset."""

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    paths: Annotated[
        list[str],
        Field(
            title="Routes for surveys",
            description=(
                "Routes relative to the source URL for each of the HiPS"
                " surveys whose properties files should be retrieved and"
                " assembled into the HiPS list"
            ),
        ),
    ]


class HipsLegacyConfig(BaseModel):
    """Configuration for the HiPS legacy path.

    This is deprecated and support will be dropped entirely once the Rubin
    dataset available under the legacy paths is retired.
    """

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    dataset: Annotated[
        str | None,
        Field(
            title="Dataset to show under legacy path",
            description=(
                "Label of the HiPS dataset that's also exported under the"
                " legacy path. Set to None if legacy paths are not supported."
            ),
        ),
    ] = None

    path_prefix: Annotated[
        str,
        Field(
            title="Path prefix for legacy HiPS path",
            description=(
                "Path prefix for the legacy HiPS path, which only supports a"
                " single databaset"
            ),
        ),
    ]


class HipsConfig(BaseModel):
    """Configuration for HiPS datasets.

    This is used to generate service discovery information for HiPS datasets
    and to configure the Repertoire server, which provides combined HiPS list
    files built from the properties files of the datasets for the individual
    bands.
    """

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    datasets: Annotated[
        dict[str, HipsDatasetConfig],
        Field(
            title="Label to HiPS config mapping",
            description=(
                "Mapping of dataset labels to the corresponding HiPS list"
                " configuration"
            ),
        ),
    ]

    legacy: Annotated[
        HipsLegacyConfig | None,
        Field(
            title="Legacy HiPS configuration",
            description=(
                "Configuration for the HiPS legacy path. This is provided only"
                " for backward compatibility and will be dropped in a future"
                " release."
            ),
        ),
    ] = None

    path_prefix: Annotated[
        str,
        Field(
            title="HiPS list path prefix",
            description=(
                "Path prefix for the the list files for per-dataset HiPS"
                " collections. /<dataset>/list will be appended."
            ),
        ),
    ]

    source_template: Annotated[
        str,
        Field(
            title="Source URL template",
            description=(
                "Template for the URL for the HiPS survey, used to retrieve"
                " the properties files to construct the HiPS list"
            ),
        ),
    ]


class InfluxDatabaseConfig(BaseModel):
    """Configuration for an InfluxDB database.

    Since these vary by environment and may be accessible across environments,
    they need to be specified separately in each environment.
    """

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    url: Annotated[
        HttpUrl,
        Field(
            title="InfluxDB URL",
            description="URL of InfluxDB service",
            examples=["https://example.cloud/influxdb/"],
        ),
    ]

    database: Annotated[
        str,
        Field(
            title="Name of InfluxDB database",
            description="Name of database to include in queries",
            examples=["efd", "lsst.square.metrics"],
        ),
    ]

    username: Annotated[
        str,
        Field(
            title="Client username",
            description="Username to send for authentication",
            examples=["efdreader"],
        ),
    ]

    password_key: Annotated[
        str,
        Field(
            title="Secret key containing password",
            description=(
                "Set this to the key of the secret containing the password"
                " for this InfluxDB database"
            ),
            examples=["influxdb_efd-password"],
        ),
    ]

    schema_registry: Annotated[
        HttpUrl,
        Field(
            title="Schema registry URL",
            description="URL of corresponding Confluent schema registry",
            examples=["https://example.cloud/schema-registry"],
        ),
    ]


class ApiVersionRule(BaseModel):
    """Discovery generation rule for one API version."""

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    template: Annotated[
        str,
        Field(
            title="Template", description="Jinja template to generate the URL"
        ),
    ]

    ivoa_standard_id: Annotated[
        str | None,
        Field(
            title="IVOA standardID",
            description="IVOA standardID used in service registrations",
        ),
    ] = None


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


class VersionedServiceRule(BaseRule):
    """Base class for services that can have multiple API versions."""

    versions: Annotated[
        dict[str, ApiVersionRule],
        Field(
            title="API versions",
            description=(
                "Mapping of API version names to discovery information for"
                " that API version"
            ),
        ),
    ] = {}


class DataServiceRule(VersionedServiceRule):
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

    openapi: Annotated[
        str | None,
        Field(
            title="OpenAPI schema template",
            description="Template to generate the OpenAPI schema URL",
        ),
    ] = None


class InternalServiceRule(VersionedServiceRule):
    """Rule for an internal Phalanx service not associated with a dataset."""

    type: Annotated[Literal["internal"], Field(title="Type of service")]

    openapi: Annotated[
        str | None,
        Field(
            title="OpenAPI schema template",
            description="Template to generate the OpenAPI schema URL",
        ),
    ] = None


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

    available_datasets: Annotated[
        set[str],
        Field(
            title="Available datasets",
            description="Datasets available in this Phalanx environment",
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
        dict[str, DatasetConfig],
        Field(
            title="Datasets",
            description=(
                "Mapping of dataset names to metadata about that dataset"
            ),
        ),
    ] = {}

    hips: Annotated[
        HipsConfig | None,
        Field(
            title="HiPS list configuration",
            description="URL and band information for HiPS datasets",
        ),
    ] = None

    influxdb_databases: Annotated[
        dict[str, InfluxDatabaseConfig],
        Field(
            title="InfluxDB databases",
            description=(
                "Mapping of short database names to InfluxDB database"
                " connection information for databases accessible from this"
                " Phalanx environment"
            ),
        ),
    ] = {}

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
