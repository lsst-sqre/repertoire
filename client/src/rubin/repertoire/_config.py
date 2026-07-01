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
    "ApiVersionRule",
    "BaseRegistryEntry",
    "BaseRule",
    "DataServiceRule",
    "DatasetConfig",
    "DatasetRegistryEntry",
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
    "RegistryEntry",
    "RepertoireSettings",
    "Rule",
    "SiaRegistryEntry",
    "SodaRegistryEntry",
    "TapDatasetEntry",
    "TapOutputFormatConfig",
    "TapRegistryEntry",
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

    docs_url: Annotated[
        HttpUrl | None,
        Field(
            title="Documentation URL",
            description="URL to more detailed documentation about the dataset",
        ),
    ] = None


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

    facility: Annotated[
        list[str],
        Field(
            title="Facility names",
            description=(
                "Observatory or facility names for this record. When set,"
                " this overrides the global facility default."
            ),
        ),
    ] = []

    instrument: Annotated[
        list[str],
        Field(
            title="Instrument names",
            description="Instrument names associated with this record.",
        ),
    ] = []


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
                raise ValueError(
                    f"Rule '{self.name}' has a duplicate standard ID"
                    f" '{rule.ivoa_standard_id}'"
                )
            seen.add(rule.ivoa_standard_id)

        # If generating IVOA registry information, make sure the SODA and SIA
        # rules, which require specific IVOA standard IDs in their version
        # entries, are complete.
        match self.ivoa_registry:
            case GmsRegistryEntry():
                if self.version_for_id(IvoaStandardId.GMS_SEARCH_1) is None:
                    raise ValueError(
                        f"GMS rule '{self.name}' must have a version with"
                        f" standard ID '{IvoaStandardId.GMS_SEARCH_1}'"
                    )
            case SiaRegistryEntry():
                if self.version_for_id(IvoaStandardId.SIA_QUERY_2) is None:
                    raise ValueError(
                        f"SIA rule '{self.name}' must have a version with"
                        f" standard ID '{IvoaStandardId.SIA_QUERY_2}'"
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
                    raise ValueError(
                        f"SODA rule '{self.name}' missing standard IDs: "
                        f"{missing_str}"
                    )
            case _:
                pass

        # Validation succeeded.
        return self


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

    environment_name: Annotated[
        str | None,
        Field(
            title="Name of environment",
            description=(
                "Human-readable name of the environment, intended for use"
                " in status or error reporting. This may be a hostname if"
                " that is the most descriptive name, but should not be"
                " assumed to be a hostname or used to construct any URLs."
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
