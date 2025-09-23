"""Client, models, and URL construction for Repertoire."""

from ._builder import RepertoireBuilder, RepertoireBuilderWithSecrets
from ._client import DiscoveryClient
from ._config import (
    BaseRule,
    DataServiceRule,
    DatasetConfig,
    InfluxDatabaseConfig,
    InternalServiceRule,
    RepertoireSettings,
    UiServiceRule,
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
    "BaseRule",
    "BaseService",
    "DataService",
    "DataServiceRule",
    "Dataset",
    "DatasetConfig",
    "Discovery",
    "DiscoveryClient",
    "DiscoveryDependency",
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
    "Services",
    "UiService",
    "UiServiceRule",
    "discovery_dependency",
    "register_mock_discovery",
]
