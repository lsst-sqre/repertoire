"""Construct service discovery information from configuration."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Template
from pydantic import HttpUrl, SecretStr

from ._config import (
    DataServiceRule,
    InternalServiceRule,
    RepertoireSettings,
    Rule,
    UiServiceRule,
)
from ._models import (
    DataService,
    Dataset,
    Discovery,
    InfluxDatabase,
    InfluxDatabaseWithCredentials,
    InfluxDatabaseWithPointer,
    InternalService,
    Services,
    UiService,
)

__all__ = [
    "RepertoireBuilder",
    "RepertoireBuilderWithSecrets",
]


class RepertoireBuilder:
    """Construct service discovery information from configuration.

    This class is responsible for turning a Repertoire configuration, which
    contains information about a given Phalanx environment plus generic URL
    construction rules for Phalanx applications, into Repertoire service
    discovery information suitable for returning to a client.

    Parameters
    ----------
    config
        Repertoire configuration.
    """

    def __init__(self, config: RepertoireSettings) -> None:
        self._config = config
        self._base_context = {"base_hostname": config.base_hostname}

    def build_discovery(
        self, base_url: str, hips_base_url: str | None = None
    ) -> Discovery:
        """Construct service discovery information from the configuration.

        Parameters
        ----------
        base_url
            Base URL for Repertoire internal links.
        hips_base_url
            Base URL for HiPS list files, without any part of the HiPS path
            prefixes, or `None` to not consider HiPS information.

        Returns
        -------
        Discovery
            Service discovery information.
        """
        return Discovery(
            applications=sorted(self._config.applications),
            datasets=self._build_datasets(hips_base_url),
            influxdb_databases=self._build_influxdb_databases(base_url),
            services=self._build_services(),
        )

    def build_influxdb(self, database: str) -> InfluxDatabase | None:
        """Construct InfluxDB discovery information from the configuration.

        Parameters
        ----------
        database
            Name of the InfluxDB database.
        include_credentials
            If set to `True`, include credential information. This requires
            the credential secrets be available locally to where this code
            is running, at the configured paths.

        Returns
        -------
        InfluxDatabase or None
            InfluxDB connection information or `None` if no such InfluxDB
            database was found.
        """
        influxdb = self._config.influxdb_databases.get(database)
        if not influxdb:
            return None
        return InfluxDatabase(
            url=influxdb.url,
            database=influxdb.database,
            schema_registry=influxdb.schema_registry,
        )

    def _build_datasets(self, base_url: str | None) -> dict[str, Dataset]:
        """Construct the datasets available in an environment."""
        results = {}
        for key, value in self._config.datasets.items():
            if key not in self._config.available_datasets:
                continue
            hips = None
            if base_url and self._config.hips:
                if key in self._config.hips.datasets:
                    path_prefix = self._config.hips.path_prefix
                    hips_base_url = base_url.rstrip("/") + path_prefix
                    hips = HttpUrl(hips_base_url + f"/{key}/list")
            results[key] = Dataset(
                butler_config=self._config.butler_configs.get(key),
                description=value.description,
                hips_list=hips,
            )
        return results

    def _build_influxdb_databases(
        self, base_url: str
    ) -> dict[str, InfluxDatabaseWithPointer]:
        """Construct the URLs to credentials for InfluxDB databases."""
        result = {}
        for label, config in sorted(self._config.influxdb_databases.items()):
            creds_url = base_url.rstrip("/") + f"/discovery/influxdb/{label}"
            result[label] = InfluxDatabaseWithPointer(
                url=config.url,
                database=config.database,
                schema_registry=config.schema_registry,
                credentials_url=HttpUrl(creds_url),
            )
        return result

    def _build_services(self) -> Services:
        """Construct the service URLs for an environment."""
        services = Services()
        for application in sorted(self._config.applications):
            if application in self._config.use_subdomains:
                rules = self._config.subdomain_rules.get(application, [])
            else:
                rules = self._config.rules.get(application, [])
            for rule in rules:
                self._build_service_from_rule(application, rule, services)
        return services

    def _build_service_from_rule(
        self, name: str, rule: Rule, services: Services
    ) -> None:
        """Generate and store service information based on a rule.

        Parameters
        ----------
        name
            Name of the application.
        rule
            Generation rule for the service information.
        services
            Collected service information into which to insert the result.
        """
        if rule.name:
            name = rule.name
        match rule:
            case DataServiceRule():
                allowed = rule.datasets or self._config.available_datasets
                for dataset in allowed:
                    if dataset not in self._config.available_datasets:
                        continue
                    service = self._build_data_service_from_rule(dataset, rule)
                    if name not in services.data:
                        services.data[name] = {}
                    services.data[name][dataset] = service
            case InternalServiceRule():
                internal_service = self._build_internal_service_from_rule(rule)
                services.internal[name] = internal_service
            case UiServiceRule():
                services.ui[name] = self._build_ui_service_from_rule(rule)

    def _build_dataset_context(self, dataset: str) -> dict[str, str]:
        """Construct a Jinja template context for a given dataset."""
        return {**self._base_context, "dataset": dataset}

    def _build_data_service_from_rule(
        self, dataset: str, rule: DataServiceRule
    ) -> DataService:
        """Generate data service information based on a rule.

        Parameters
        ----------
        dataset
            Name of the dataset.
        rule
            Generation rule for the service information.

        Returns
        -------
        DataService
            Constructed service information.
        """
        context = self._build_dataset_context(dataset)
        openapi = None
        if rule.openapi:
            openapi = HttpUrl(Template(rule.openapi).render(**context))
        return DataService(
            url=HttpUrl(Template(rule.template).render(**context)),
            openapi=openapi,
        )

    def _build_internal_service_from_rule(
        self, rule: InternalServiceRule
    ) -> InternalService:
        """Generate internal service information based on a rule.

        Parameters
        ----------
        rule
            Generation rule for the service information.

        Returns
        -------
        InternalService
            Constructed service information.
        """
        openapi = None
        if rule.openapi:
            openapi_str = Template(rule.openapi).render(**self._base_context)
            openapi = HttpUrl(openapi_str)
        return InternalService(
            url=HttpUrl(Template(rule.template).render(**self._base_context)),
            openapi=openapi,
        )

    def _build_ui_service_from_rule(self, rule: UiServiceRule) -> UiService:
        """Generate UI service information based on a rule.

        Parameters
        ----------
        rule
            Generation rule for the service information.

        Returns
        -------
        UiService
            Constructed service information.
        """
        return UiService(
            url=HttpUrl(Template(rule.template).render(**self._base_context))
        )


class RepertoireBuilderWithSecrets(RepertoireBuilder):
    """Construct service discovery from configuration with secrets.

    This class is identical to `RepertoireBuilder` with the addition of local
    secrets. This allows it to build discovery information that requires
    secrets, such as InfluxDB connection information with credentials.

    Parameters
    ----------
    config
        Repertoire configuration.
    secrets_root
        Root path to where Repertoire secrets are stored.
    """

    def __init__(
        self, config: RepertoireSettings, secrets_root: str | Path
    ) -> None:
        super().__init__(config)
        self._secrets_root = Path(secrets_root)

    def build_influxdb_with_credentials(
        self, database: str
    ) -> InfluxDatabaseWithCredentials | None:
        """Construct InfluxDB discovery information with credentials.

        The files referenced in the password paths must exist locally when
        calling this method. This will be the case for the running Repertoire
        service but not when the library is being called outside of the
        service, such as when building static information.

        Parameters
        ----------
        database
            Name of the InfluxDB database.

        Returns
        -------
        InfluxDatabase or None
            InfluxDB connection information or `None` if no such InfluxDB
            database was found.
        """
        influxdb = self._config.influxdb_databases.get(database)
        if not influxdb:
            return None
        password_path = self._secrets_root / influxdb.password_key
        password = password_path.read_text()
        return InfluxDatabaseWithCredentials(
            url=influxdb.url,
            database=influxdb.database,
            username=influxdb.username,
            password=SecretStr(password.rstrip("\n")),
            schema_registry=influxdb.schema_registry,
        )
