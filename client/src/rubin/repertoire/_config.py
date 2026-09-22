"""Configuration model for Repertoire."""

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal, Self

import yaml
from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    model_validator,
)
from pydantic.alias_generators import to_camel
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    "ApiServiceOverride",
    "ApiServiceRule",
    "ApiVersionRule",
    "BaseRegistryEntry",
    "BaseServiceRule",
    "DataServiceRule",
    "DatasetConfig",
    "DatasetRegistryEntry",
    "EnvironmentConfig",
    "GmsRegistryEntry",
    "HipsConfig",
    "HipsDatasetConfig",
    "HipsLegacyConfig",
    "InfluxDatabaseConfig",
    "InternalServiceRule",
    "IvoaContentLevel",
    "IvoaContentType",
    "IvoaStandardId",
    "MultiRecordRegistryEntry",
    "QuotaLabelConfig",
    "RegistryEntry",
    "RepertoireSettings",
    "ServiceConfig",
    "ServiceOverride",
    "ServiceOverrides",
    "ServiceRules",
    "SiaRegistryEntry",
    "SodaRegistryEntry",
    "TapDatasetEntry",
    "TapOutputFormatConfig",
    "TapRegistryEntry",
    "UiServiceRule",
]


class EnvironmentConfig(BaseModel):
    """General information about the local Phalanx environment."""

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    name: Annotated[
        str,
        Field(
            title="Name of environment",
            description=(
                "Human-readable name of the environment, intended for use"
                " in status or error reporting. This may be a hostname if"
                " that is the most descriptive name, but should not be"
                " assumed to be a hostname or used to construct any URLs."
            ),
        ),
    ]

    label: Annotated[
        str,
        Field(
            title="Phalanx label",
            description="Phalanx environment name for this environment",
        ),
    ]

    title: Annotated[
        str | None,
        Field(
            title="Short title",
            description=(
                "Short human-readable title of the environment. If not set,"
                " name is used instead."
            ),
        ),
    ] = None

    title_long: Annotated[
        str | None,
        Field(
            title="Long title",
            description=(
                "Full human-readable title of the environment. If not set,"
                " title is used instead, or name if title is not set."
            ),
        ),
    ] = None

    description: Annotated[
        str | None,
        Field(
            title="Description",
            description="Human-readable description of the environment",
        ),
    ] = None

    docs_url: Annotated[
        HttpUrl,
        Field(
            title="Documentation URL",
            description=(
                "URL to additional documentation about the environment"
            ),
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


class QuotaLabelConfig(BaseModel):
    """Configuration for a quota label."""

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    title: Annotated[str, Field(title="Short description")]

    internal: Annotated[
        bool,
        Field(
            title="Whether quota is internal",
            description=(
                "If true, the quota rule should be hidden from user-facing"
                " quota summaries"
            ),
        ),
    ] = False


class ServiceConfig(BaseModel):
    """Base configuration for any service."""

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    title: Annotated[
        str | None,
        Field(
            title="Short description",
            description="Short human-readable description of the service",
        ),
    ] = None

    docs_url: Annotated[
        HttpUrl | None,
        Field(
            title="Documentation URL",
            description="URL to service documentation",
        ),
    ] = None

    required_scopes: Annotated[
        list[str],
        Field(
            title="Required scopes",
            description=(
                "Required scopes to access this service. If more than one is"
                " listed, all listed scopes are required."
            ),
        ),
    ] = []

    quota_labels: Annotated[
        dict[str, QuotaLabelConfig],
        Field(
            title="Quota labels",
            description=(
                "Gafaelfawr API quota labels that apply to this service"
            ),
        ),
    ] = {}


class HipsConfig(ServiceConfig):
    """Configuration for HiPS datasets.

    This is used to generate service discovery information for HiPS datasets
    and to configure the Repertoire server, which provides combined HiPS list
    files built from the properties files of the datasets for the individual
    bands.
    """

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

    local: Annotated[
        bool,
        Field(
            title="Is database local",
            description="Whether the database is local to this environment",
        ),
    ] = False


class IvoaStandardId(StrEnum):
    """Known IVOA standard IDs for service capability registrations."""

    DATALINK_LINKS_1 = "ivo://ivoa.net/std/DataLink#links-1.1"
    GMS_SEARCH_1 = "ivo://ivoa.net/std/gms#search-1.0"
    HIPS_LIST_1 = "ivo://ivoa.net/std/hips#hipslist-1.0"
    SIA_QUERY_2 = "ivo://ivoa.net/std/SIA#query-2.0"
    SODA_ASYNC_1 = "ivo://ivoa.net/std/SODA#async-1.0"
    SODA_SYNC_1 = "ivo://ivoa.net/std/SODA#sync-1.0"
    VOSI_AVAILABILITY = "ivo://ivoa.net/std/VOSI#availability"
    VOSI_CAPABILITIES = "ivo://ivoa.net/std/VOSI#capabilities"
    VOSI_TABLES = "ivo://ivoa.net/std/VOSI#tables"
    TAP_AUX = "ivo://ivoa.net/std/TAP#aux"


class IvoaContentType(StrEnum):
    """IVOA controlled vocabulary for the resource content type element.

    Values are from http://www.ivoa.net/rdf/voresource/content_type.
    """

    ARCHIVE = "Archive"
    CATALOG = "Catalog"
    ORGANISATION = "Organisation"
    REGISTRY = "Registry"
    SURVEY = "Survey"


class IvoaContentLevel(StrEnum):
    """IVOA controlled vocabulary for the resource content level element.

    Values are from http://www.ivoa.net/rdf/voresource/content_level.
    """

    AMATEUR = "Amateur"
    EDUCATION = "Education"
    RESEARCH = "Research"


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
        IvoaStandardId | None,
        Field(
            title="IVOA standardID",
            description="IVOA standardID used in service registrations",
        ),
    ] = None


class BaseServiceRule(ServiceConfig):
    """Base class for rules for deriving URLs."""

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    template: Annotated[
        str,
        Field(
            title="Template", description="Jinja template to generate the URL"
        ),
    ]


class ApiServiceRule(BaseServiceRule):
    """Base class for services that can have multiple API versions."""

    openapi: Annotated[
        str | None,
        Field(
            title="OpenAPI schema template",
            description="Template to generate the OpenAPI schema URL",
        ),
    ] = None

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


class BaseRegistryEntry(BaseModel):
    """Shared fields for all IVOA registry entries."""

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    ivoid: Annotated[
        AnyUrl,
        Field(title="IVOA ID", description="IVOA identifier of the service"),
    ]

    created: Annotated[
        datetime,
        Field(
            title="Creation timestamp",
            description=(
                "When the service was first published, set once and never"
                " changed"
            ),
        ),
    ]

    description: Annotated[
        str,
        Field(
            title="Description",
            description="Long description of the service",
        ),
    ]

    title: Annotated[
        str,
        Field(
            title="Title",
            description="Title of the service",
        ),
    ]

    docs_url: Annotated[
        HttpUrl | None,
        Field(
            title="Documentation URL",
            description=(
                "URL of a human-readable page describing the service"
            ),
        ),
    ] = None

    subjects: Annotated[
        list[str],
        Field(
            title="Subject keywords",
            description=(
                "Subject keywords for this record. These are appended to any"
                " global default subjects configured on the registry."
            ),
        ),
    ] = []

    facilities: Annotated[
        list[str],
        Field(
            title="Facility names",
            description=(
                "Observatory or facility names for this record. When set,"
                " this overrides the global facility default."
            ),
        ),
    ] = []

    instruments: Annotated[
        list[str],
        Field(
            title="Instrument names",
            description="Instrument names associated with this record.",
        ),
    ] = []


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

    docs_url: Annotated[
        HttpUrl | None,
        Field(
            title="Documentation URL",
            description="URL to more detailed documentation about the dataset",
        ),
    ] = None

    ivoa_registry: Annotated[
        BaseRegistryEntry | None,
        Field(
            title="IVOA registry entry",
            description=(
                "If set, publishes a vs:DataResource record for this dataset,"
                " serving as the resolvable registry target for Butler"
                " datasets and HiPS survey IVOIDs."
            ),
        ),
    ] = None


class GmsRegistryEntry(BaseRegistryEntry):
    """IVOA registry entry for GMS (Group Membership Service)."""

    ivoa_service_type: Literal["gms"]


class SodaRegistryEntry(BaseRegistryEntry):
    """IVOA registry entry for a SODA image cutout service."""

    ivoa_service_type: Literal["soda"]


class TapOutputFormatConfig(BaseModel):
    """TAP output format."""

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    mime: Annotated[str, Field(title="MIME type")]

    alias: Annotated[
        list[str],
        Field(
            title="Aliases",
            description="Alternative FORMAT values for this MIME type.",
        ),
    ] = []


class TapDatasetEntry(BaseRegistryEntry):
    """IVOA registry entry for a dataset published via a TAP service.

    This is used for per-dataset ``vs:CatalogResource`` records that link
    back to the TAP service that serves it.
    """


class TapRegistryEntry(BaseRegistryEntry):
    """IVOA registry entry for a TAP service."""

    ivoa_service_type: Literal["tap"]

    adql_version: Annotated[
        str,
        Field(
            title="ADQL version",
            description=(
                "Version of ADQL supported by the TAP service, used in TAP"
                " registry entries"
            ),
        ),
    ] = "2.1"

    upload_supported: Annotated[
        bool,
        Field(
            title="Upload support",
            description="Whether the TAP service supports table uploads",
        ),
    ] = True

    additional_output_formats: Annotated[
        list[TapOutputFormatConfig],
        Field(
            title="Additional output formats",
            description=(
                "Additional output formats supported by this TAP service,"
                " beyond VOTable XML. Used to advertise formats such as"
                " VOParquet."
            ),
        ),
    ] = []

    datasets: Annotated[
        dict[str, TapDatasetEntry],
        Field(
            title="Per-dataset registry entries",
            description=(
                "Mapping of dataset names to catalog resource entries."
                " Each entry is published as a vs:CatalogResource record."
            ),
        ),
    ] = {}

    @model_validator(mode="after")
    def _validate_dataset_ivoids(self) -> Self:
        for name, entry in self.datasets.items():
            if entry.ivoid == self.ivoid:
                raise ValueError(
                    f"Dataset '{name}' has the same IVOID as the TAP"
                    f" service itself ({self.ivoid})"
                )
        return self


type RegistryEntry = Annotated[
    GmsRegistryEntry | SiaRegistryEntry | SodaRegistryEntry | TapRegistryEntry,
    Field(discriminator="ivoa_service_type"),
]


class MultiRecordRegistryEntry(BaseModel):
    """Base for registry entries that produce one record per dataset."""

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    records: Annotated[
        dict[str, BaseRegistryEntry],
        Field(
            title="Per-dataset registry entries",
            description=(
                "Mapping of dataset names to the IVOA registry entry for"
                " that dataset"
            ),
        ),
    ]


class SiaRegistryEntry(MultiRecordRegistryEntry):
    """Config-time IVOA registry entry for an SIA service.

    One rule covers multiple datasets. Each dataset's IVOID and metadata are
    stored separately in ``records``. The builder will resolve this into a
    `SiaDatasetRegistryEntry` per dataset when building
    `~rubin.repertoire.Discovery`.
    """

    ivoa_service_type: Literal["sia"]


class SiaDatasetRegistryEntry(BaseRegistryEntry):
    """Resolved per-dataset SIA registry entry, stored on `DataService`."""

    ivoa_service_type: Literal["sia"]


type DatasetRegistryEntry = Annotated[
    GmsRegistryEntry
    | SiaDatasetRegistryEntry
    | SodaRegistryEntry
    | TapRegistryEntry,
    Field(discriminator="ivoa_service_type"),
]


class DataServiceRule(ApiServiceRule):
    """Rule for a Phalanx service associated with a dataset."""

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

    ivoa_registry: Annotated[
        RegistryEntry | None,
        Field(
            title="IVOA registry entry",
            description=(
                "IVOA registry entry for this service. The type of entry"
                " determines the kind of IVOA record produced."
            ),
        ),
    ] = None

    def ivoa_standard_ids(self) -> set[IvoaStandardId]:
        """IVOA standard IDs for all provided standardized APIs."""
        return {
            v.ivoa_standard_id
            for v in self.versions.values()
            if v.ivoa_standard_id is not None
        }

    def version_for_id(
        self, ivoa_standard_id: IvoaStandardId
    ) -> ApiVersionRule | None:
        """Get the API rule for a specific IVOA standards version.

        Parameters
        ----------
        ivoa_standards_version
            IVOA standards version to search for.

        Returns
        -------
        ApiVersionRule or None
            Corresponding `ApiVersionRule`, or `None` if none was found.
        """
        # It is safe to return the first matching entry since the model
        # validator ensures the service doesn't provide the same IVOA standard
        # ID on multiple endpoints.
        for rule in self.versions.values():
            if rule.ivoa_standard_id == ivoa_standard_id:
                return rule
        return None

    @model_validator(mode="after")
    def _validate_ivoa_standard_ids(self) -> Self:
        # Ensure there are no duplicate IVOA standard IDs. Generating IVOA
        # registry information requires a unique rule per standards ID.
        seen = set()
        for rule in self.versions.values():
            if rule.ivoa_standard_id is None:
                continue
            if rule.ivoa_standard_id in seen:
                msg = f"duplicate standard ID '{rule.ivoa_standard_id}'"
                raise ValueError(msg)
            seen.add(rule.ivoa_standard_id)

        # If generating IVOA registry information, make sure the SODA and SIA
        # rules, which require specific IVOA standard IDs in their version
        # entries, are complete.
        match self.ivoa_registry:
            case GmsRegistryEntry():
                if self.version_for_id(IvoaStandardId.GMS_SEARCH_1) is None:
                    raise ValueError(
                        "GMS rule must have a version with standard ID"
                        f" '{IvoaStandardId.GMS_SEARCH_1}'"
                    )
            case SiaRegistryEntry():
                if self.version_for_id(IvoaStandardId.SIA_QUERY_2) is None:
                    raise ValueError(
                        "SIA rule must have a version with standard ID"
                        f" '{IvoaStandardId.SIA_QUERY_2}'"
                    )
            case SodaRegistryEntry():
                soda_ids = {
                    IvoaStandardId.SODA_SYNC_1,
                    IvoaStandardId.SODA_ASYNC_1,
                }
                version_ids = self.ivoa_standard_ids()
                missing = soda_ids - version_ids
                if missing:
                    missing_str = ", ".join(sorted(missing))
                    msg = f"SODA rule missing standard IDs: {missing_str}"
                    raise ValueError(msg)
            case _:
                pass

        # Validation succeeded.
        return self


class InternalServiceRule(ApiServiceRule):
    """Rule for an internal Phalanx service not associated with a dataset."""


class UiServiceRule(BaseServiceRule):
    """Rule for a UI Phalanx service accessed via a web browser."""


class ServiceRules(BaseSettings):
    """Rules for services registered with service discovery."""

    data: Annotated[
        dict[str, DataServiceRule], Field(title="Data services")
    ] = {}

    internal: Annotated[
        dict[str, InternalServiceRule], Field(title="Internal services")
    ] = {}

    ui: Annotated[dict[str, UiServiceRule], Field(title="UI services")] = {}


class ServiceOverride(BaseModel):
    """Override to apply atop another rule, changing only the URLs."""

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    template: Annotated[
        str,
        Field(
            title="Template", description="Jinja template to generate the URL"
        ),
    ]


class ApiVersionOverride(BaseModel):
    """URL override for one API version."""

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", validate_by_name=True
    )

    template: Annotated[
        str,
        Field(
            title="Template", description="Jinja template to generate the URL"
        ),
    ]


class ApiServiceOverride(ServiceOverride):
    """Overrides for URLs for specific API versions."""

    openapi: Annotated[
        str | None,
        Field(
            title="OpenAPI schema template",
            description="Template to generate the OpenAPI schema URL",
        ),
    ] = None

    versions: Annotated[
        dict[str, ApiVersionOverride],
        Field(
            title="API versions",
            description=(
                "Mapping of API version names to URLs for that API version"
            ),
        ),
    ] = {}


class ServiceOverrides(BaseSettings):
    """URL overrides for services registered with service discovery."""

    data: Annotated[
        dict[str, ApiServiceOverride], Field(title="Data services")
    ] = {}

    internal: Annotated[
        dict[str, ApiServiceOverride], Field(title="Internal services")
    ] = {}

    ui: Annotated[dict[str, ServiceOverride], Field(title="UI services")] = {}


class RepertoireSettings(BaseSettings):
    """Base configuration from which Repertoire constructs URLs.

    This roughly represents the merged Phalanx configuration of the Repertoire
    service for a given environment, and is also used during the Phalanx build
    process to build static service discovery information. It is defined with
    ``pydantic_settings.BaseSettings`` as the base class instead of
    ``pydantic.BaseModel`` so that the main settings class of the Repertoire
    server can inherit from it.
    """

    # Do not forbid extra attributes so that this class can be used to parse
    # the Repertoire configuration directly from its Phalanx Helm values file,
    # which contains additional settings for the Repertoire server that should
    # be ignored. The Repertoire server configuration based on this class
    # should set extra="forbid" to catch configuration errors.
    model_config = SettingsConfigDict(
        alias_generator=to_camel, validate_by_name=True
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

    environment: Annotated[
        EnvironmentConfig | None,
        Field(
            title="Enviroment metadata",
            description="Metadata about the local environment",
        ),
    ] = None

    environment_name: Annotated[
        str | None,
        Field(
            title="Name of environment",
            description=(
                "Human-readable name of the environment, intended for use"
                " in status or error reporting. This may be a hostname if"
                " that is the most descriptive name, but should not be"
                " assumed to be a hostname or used to construct any URLs."
                " Deprecated in favor of environment.name, but used if that"
                " setting doesn't exist."
            ),
        ),
    ] = None

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

    obscore_configs: Annotated[
        dict[str, HttpUrl],
        Field(
            title="ObsCore exporter config URLs",
            description=(
                "URLs to the configuration used by the SIAv2 service to"
                " convert Butler records to ObsCore, if it is available for"
                " this dataset"
            ),
            examples=[{"dp2": "https://example.com/obscore/dp2.yaml"}],
        ),
    ] = {}

    rules: Annotated[
        dict[str, ServiceRules],
        Field(
            title="Phalanx service rules",
            description=(
                "Rules mapping Phalanx application names to services and"
                " instructions for what to include in service discovery for"
                " that service. These rules are used if the service is not"
                " running on a subdomain."
            ),
        ),
    ] = {}

    subdomain_overrides: Annotated[
        dict[str, ServiceOverrides],
        Field(
            title="Phalanx subdomain URL overrides",
            description=(
                "Mapping of Phalanx application names to URL overrides that"
                " should be applied if this service is running on a subdomain"
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
