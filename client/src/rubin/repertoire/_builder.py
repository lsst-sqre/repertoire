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
    Dataset,
    Discovery,
    InfluxDatabase,
    InfluxDatabaseWithCredentials,
    ServiceUrls,
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
        self._datasets = {d.name for d in config.datasets}

    def build_discovery(self, base_url: str) -> Discovery:
        """Construct service discovery information from the configuration.

        Parameters
        ----------
        base_url
            Base URL for Repertoire internal links.

        Returns
        -------
        Discovery
            Service discovery information.
        """
        return Discovery(
            applications=sorted(self._config.applications),
            datasets=self._build_datasets(),
            influxdb_databases=self._build_influxdb_databases(base_url),
            urls=self._build_urls(),
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

    def _build_datasets(self) -> list[Dataset]:
        """Construct the datasets available in an environment."""
        datasets = [Dataset(name=d) for d in sorted(self._datasets)]
        for dataset in datasets:
            name = dataset.name
            if name in self._config.butler_configs:
                dataset.butler_config = self._config.butler_configs[name]
        return datasets

    def _build_influxdb_databases(self, base_url: str) -> dict[str, HttpUrl]:
        """Construct the URLs to credentials for InfluxDB databases."""
        return {
            k: HttpUrl(base_url.rstrip("/") + f"/discovery/influxdb/{k}")
            for k, v in sorted(self._config.influxdb_databases.items())
        }

    def _build_urls(self) -> ServiceUrls:
        """Construct the service URLs for an environment."""
        urls = ServiceUrls()
        for application in sorted(self._config.applications):
            if application in self._config.use_subdomains:
                rules = self._config.subdomain_rules.get(application, [])
            else:
                rules = self._config.rules.get(application, [])
            for rule in rules:
                self._build_url_from_rule(application, rule, urls)
        return urls

    def _build_url_from_rule(
        self, name: str, rule: Rule, urls: ServiceUrls
    ) -> None:
        """Generate and store URLs based on a rule.

        Parameters
        ----------
        name
            Name of the application.
        rule
            Generation rule for the URL.
        urls
            Collected URLs into which to insert the result.
        """
        if rule.name:
            name = rule.name
        template = Template(rule.template)
        context = self._base_context
        match rule:
            case DataServiceRule():
                for dataset in rule.datasets or self._datasets:
                    if dataset not in self._datasets:
                        continue
                    context = {**context, "dataset": dataset}
                    url = template.render(**context)
                    if name not in urls.data:
                        urls.data[name] = {}
                    urls.data[name][dataset] = HttpUrl(url)
            case InternalServiceRule():
                urls.internal[name] = HttpUrl(template.render(**context))
            case UiServiceRule():
                urls.ui[name] = HttpUrl(template.render(**context))


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
