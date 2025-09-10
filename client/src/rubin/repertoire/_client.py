"""Client for service discovery."""

from __future__ import annotations

import os

from httpx import AsyncClient, HTTPError
from pydantic import BaseModel, HttpUrl, ValidationError

from ._exceptions import (
    RepertoireUrlError,
    RepertoireValidationError,
    RepertoireWebError,
)
from ._models import Discovery, InfluxDatabaseWithCredentials

__all__ = ["DiscoveryClient"]


class DiscoveryClient:
    """Client for Phalanx service and dataset discovery.

    Services that want to discover Phalanx services and datasets and that are
    not using the IVOA discovery protocols should use this client. Software
    running on a Science Pipelines stack container should instead use the
    client provided by ``lsst.rsp``.

    Discovery information is cached inside this client where appropriate.
    Callers should call the methods on this object each time discovery
    information is needed and not cache the results locally.

    Normally, the environment variable ``REPERTOIRE_BASE_URL`` should be set
    by the Phalanx chart for the application and will be used to locate the
    base URL of the Repertoire discovery service in the local Phalanx
    environment.

    Parameters
    ----------
    http_client
        Existing ``httpx.AsyncClient`` to use instead of creating a new one.
        This allows the caller to reuse an existing client and connection
        pool.
    base_url
        Base URL of Repertoire, overriding the ``REPERTOIRE_BASE_URL``
        environment variable. If this parameter is not provided and
        ``REPERTOIRE_BASE_URL`` is not set in the environment,
        `RepertoireUrlError` will be raised.
    """

    def __init__(
        self,
        http_client: AsyncClient | None = None,
        *,
        base_url: str | None = None,
    ) -> None:
        self._client = http_client or AsyncClient()
        self._discovery_cache: Discovery | None = None

        if base_url is not None:
            self._base_url = base_url.rstrip("/")
        else:
            base_url = os.getenv("REPERTOIRE_BASE_URL")
            if not base_url:
                msg = "REPERTOIRE_BASE_URL not set in environment"
                raise RepertoireUrlError(msg)
            self._base_url = base_url.rstrip("/")

    async def applications(self) -> list[str]:
        """List applications installed in the local Phalanx environment.

        Returns
        -------
        list of str
            Phalanx application names expected to be deployed in the local
            environment. This is based on Phalanx configuration as injected
            into the Repertoire service, not based on what is currently
            deployed, so some applications may be missing if the environment
            is out of sync with the configuration.

        Raises
        ------
        RepertoireError
            Raised on error fetching discovery information from Repertoire.
        """
        discovery = await self._get_discovery()
        return discovery.applications

    async def butler_config_for(self, dataset: str) -> str | None:
        """Return the Butler configuration URL for a given dataset.

        Parameters
        ----------
        dataset
            Short name of a dataset, chosen from the results of `datasets`.

        Returns
        -------
        str or None
            URL to the Butler configuration, or `None` if that dataset is
            not recognized or does not have a Butler configuration.

        Raises
        ------
        RepertoireError
            Raised on error fetching discovery information from Repertoire.
        """
        discovery = await self._get_discovery()
        for candidate in discovery.datasets:
            if candidate.name == dataset and candidate.butler_config:
                return str(candidate.butler_config)
        return None

    async def butler_repositories(self) -> dict[str, str]:
        """Return the Butler repository mapping for the local environment.

        Returns
        -------
        dict of str
            Mapping of dataset labels to Butler configuration URLs. This
            result is suitable for use as the constructor argument to
            ``lsst.daf.butler.LabeledButlerFactory``.

        Raises
        ------
        RepertoireError
            Raised on error fetching discovery information from Repertoire.
        """
        discovery = await self._get_discovery()
        return {
            d.name: str(d.butler_config)
            for d in discovery.datasets
            if d.butler_config is not None
        }

    async def datasets(self) -> list[str]:
        """List datasets available in the local Phalanx environment.

        Returns
        -------
        list of str
            Short identifiers (``dp1``, for example) of the datasets expected
            to be available in the local Phalanx environment. These are the
            valid dataset arguments to `butler_config_for` and
            `url_for_data_service`.

        Raises
        ------
        RepertoireError
            Raised on error fetching discovery information from Repertoire.
        """
        discovery = await self._get_discovery()
        return sorted(d.name for d in discovery.datasets)

    async def get_influxdb_connection_info(
        self, database: str, token: str
    ) -> InfluxDatabaseWithCredentials | None:
        """Get connection information for an InfluxDB database.

        Parameters
        ----------
        database
            Short name of the InfluxDB database. Call `influxdb_databases` to
            get the valid values.
        token
            Gafaelfawr token to use for authentication. Database information
            may only be available to users with specific scopes.

        Returns
        -------
        InfluxDatabaseWithCredentials or None
            Connection information for an InfluxDB database, including
            credentials, or `None` if this database was not found in this
            environment.

        Raises
        ------
        RepertoireError
            Raised on error fetching discovery information from Repertoire.
        """
        discovery = await self._get_discovery()
        if url := discovery.influxdb_databases.get(database):
            return await self._get(url, InfluxDatabaseWithCredentials, token)
        else:
            return None

    async def influxdb_databases(self) -> list[str]:
        """List InfluxDB databases available in the local Phalanx environment.

        These may or may not be locally hosted, but the credentials and
        connection information is available to authenticated users.

        Returns
        -------
        list of str
            Short identifiers (``summit_efd``, for example) of the available
            InfluxDB databases. This string should be passed as the
            ``database`` argument to `get_influxdb_connection_info`.

        Raises
        ------
        RepertoireError
            Raised on error fetching discovery information from Repertoire.
        """
        discovery = await self._get_discovery()
        return sorted(discovery.influxdb_databases.keys())

    async def url_for_data_service(
        self, service: str, dataset: str
    ) -> str | None:
        """Return the base API URL for a given data service.

        Parameters
        ----------
        service
            Name of the service.
        dataset
            Dataset that will be queried via the API, chosen from the results
            of `datasets`.

        Returns
        -------
        str or None
            Base URL of the API, or `None` if the service or dataset is not
            available in this environment.

        Raises
        ------
        RepertoireError
            Raised on error fetching discovery information from Repertoire.
        """
        discovery = await self._get_discovery()
        urls = discovery.urls.data.get(service)
        if not urls:
            return None
        url = urls.get(dataset)
        return str(url) if url is not None else None

    async def url_for_internal_service(self, service: str) -> str | None:
        """Return the base API URL for a given internal service.

        Parameters
        ----------
        service
            Name of the service.

        Returns
        -------
        str or None
            Base URL of the API, or `None` if the service is not available in
            this environment.

        Raises
        ------
        RepertoireError
            Raised on error fetching discovery information from Repertoire.
        """
        discovery = await self._get_discovery()
        url = discovery.urls.internal.get(service)
        return str(url) if url is not None else None

    async def url_for_ui_service(self, service: str) -> str | None:
        """Return the base URL for a given UI service.

        Parameters
        ----------
        service
            Name of the service.

        Returns
        -------
        str or None
            Base URL of the service, or `None` if the service is not available
            in this environment.

        Raises
        ------
        RepertoireError
            Raised on error fetching discovery information from Repertoire.
        """
        discovery = await self._get_discovery()
        url = discovery.urls.ui.get(service)
        return str(url) if url is not None else None

    async def _get[T: BaseModel](
        self, url: str | HttpUrl, model: type[T], token: str | None = None
    ) -> T:
        """Make an HTTP GET request and validate the results.

        Parameters
        ----------
        url
            URL at which to make the request.
        model
            Expected type of the response.
        token
            If given, authenticate with the provided Gafaelfawr token.

        Returns
        -------
        pydantic.BaseModel
            Validated model of the requested type.

        Raises
        ------
        RepertoireError
            Raised on error fetching discovery information from Repertoire.
        """
        headers = {}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        try:
            r = await self._client.get(str(url), headers=headers)
            r.raise_for_status()
            return model.model_validate(r.json())
        except HTTPError as e:
            raise RepertoireWebError.from_exception(e) from e
        except ValidationError as e:
            raise RepertoireValidationError(str(e)) from e

    async def _get_discovery(self) -> Discovery:
        """Fetch and cache discovery information."""
        if self._discovery_cache is None:
            route = self._build_url("/discovery")
            self._discovery_cache = await self._get(route, Discovery)
        return self._discovery_cache

    def _build_url(self, route: str) -> str:
        """Construct a Repertoire URL for a given route."""
        return self._base_url + route
