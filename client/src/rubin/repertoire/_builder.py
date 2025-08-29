"""Construct service discovery information from configuration."""

from __future__ import annotations

from jinja2 import Template
from pydantic import HttpUrl

from ._config import (
    DataServiceRule,
    InternalServiceRule,
    RepertoireSettings,
    Rule,
    UiServiceRule,
)
from ._models import Dataset, Discovery, ServiceUrls

__all__ = ["RepertoireBuilder"]


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

    def build(self) -> Discovery:
        """Construct service discovery information from the configuration.

        Returns
        -------
        Discovery
            Service discovery information.
        """
        return Discovery(
            applications=sorted(self._config.applications),
            datasets=self._build_datasets(),
            urls=self._build_urls(),
        )

    def _build_datasets(self) -> list[Dataset]:
        """Construct the datasets available in an environment."""
        datasets = [Dataset(name=d) for d in sorted(self._datasets)]
        for dataset in datasets:
            name = dataset.name
            if name in self._config.butler_configs:
                dataset.butler_config = self._config.butler_configs[name]
        return datasets

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
