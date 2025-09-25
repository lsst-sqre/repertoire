"""Client, models, and URL construction for Repertoire."""

from ._builder import RepertoireBuilder, RepertoireBuilderWithSecrets
from ._client import DiscoveryClient
from ._config import (
    ApiVersionRule,
    BaseRule,
    DataServiceRule,
    DatasetConfig,
    HipsConfig,
    HipsDatasetConfig,
    HipsLegacyConfig,
    InfluxDatabaseConfig,
    InternalServiceRule,
    RepertoireSettings,
    Rule,
    UiServiceRule,
    VersionedServiceRule,
)
from ._dependencies import DiscoveryDependency, discovery_dependency
from ._exceptions import (
    RepertoireError,
    RepertoireUrlError,
    RepertoireValidationError,
    RepertoireWebError,
)
from ._mock import register_mock_discovery
from ._models import (
    ApiService,
    ApiVersion,
    BaseService,
    DataService,
    Dataset,
    Discovery,
    InfluxDatabase,
    InfluxDatabaseWithCredentials,
    InternalService,
    Services,
    UiService,
)

__all__ = [
    "ApiService",
    "ApiVersion",
    "ApiVersionRule",
    "BaseRule",
    "BaseService",
    "DataService",
    "DataServiceRule",
    "Dataset",
    "DatasetConfig",
    "Discovery",
    "DiscoveryClient",
    "DiscoveryDependency",
    "HipsConfig",
    "HipsDatasetConfig",
    "HipsLegacyConfig",
    "InfluxDatabase",
    "InfluxDatabaseConfig",
    "InfluxDatabaseWithCredentials",
    "InternalService",
    "InternalServiceRule",
    "RepertoireBuilder",
    "RepertoireBuilderWithSecrets",
    "RepertoireError",
    "RepertoireSettings",
    "RepertoireUrlError",
    "RepertoireValidationError",
    "RepertoireWebError",
    "Rule",
    "Services",
    "UiService",
    "UiServiceRule",
    "VersionedServiceRule",
    "discovery_dependency",
    "register_mock_discovery",
]
