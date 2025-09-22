"""HiPS list builder and cache."""

import re
from typing import Annotated

from fastapi import Depends, Path
from httpx import AsyncClient, HTTPError
from jinja2 import Template
from safir.dependencies.logger import logger_dependency
from structlog.stdlib import BoundLogger

from ..config import Config
from ..exceptions import HipsDatasetNotFoundError, HipsWebError
from .config import config_dependency

__all__ = [
    "HipsListDependency",
    "hips_list_dependency",
]


class HipsListDependency:
    """Base class with common HiPS list functionality."""

    def __init__(self) -> None:
        self._client = AsyncClient()
        self._cache: dict[str, str] = {}

    async def __call__(
        self,
        dataset: Annotated[
            str,
            Path(
                title="Dataset label",
                description="Short label for the dataset",
                examples=["dp02", "dp1"],
            ),
        ],
        *,
        config: Annotated[Config, Depends(config_dependency)],
        logger: Annotated[BoundLogger, Depends(logger_dependency)],
    ) -> str:
        return await self.get_list(dataset, config, logger)

    def clear_cache(self) -> None:
        """Clear the cached HiPS data."""
        self._cache = {}

    async def get_list(
        self, dataset: str, config: Config, logger: BoundLogger
    ) -> str:
        """Get the HiPS list for a dataset, with possible caching.

        This dependency can only be used from a route that defines ``dataset``
        as a path parameter.

        Parameters
        ----------
        dataset
            Dataset for which to construct a HiPS list.
        config
            Repertoire configuration.
        logger
            Logger for error messages.

        Returns
        -------
        str
            HiPS list content.

        Raises
        ------
        HipsDatasetNotFoundError
            Raised if the requested dataset has no HiPS configuration.
        HipsWebError
            Raised if an error was encountered retrieving the underlying
            properties file.
        """
        if dataset in self._cache:
            return self._cache[dataset]
        logger = logger.bind(dataset=dataset)
        result = await self._build_hips_list(config, dataset, logger)
        self._cache[dataset] = result
        return result

    async def legacy(
        self,
        *,
        config: Annotated[Config, Depends(config_dependency)],
        logger: Annotated[BoundLogger, Depends(logger_dependency)],
    ) -> str:
        """Get the legacy HiPS list, if configured.

        Intended for use as a FastAPI dependency.
        """
        if not config.hips or not config.hips.legacy:
            raise HipsDatasetNotFoundError("Legacy HiPS list not configured")
        if not config.hips.legacy.dataset:
            raise HipsDatasetNotFoundError("Legacy HiPS list not configured")
        dataset = config.hips.legacy.dataset
        if dataset not in config.available_datasets:
            raise HipsDatasetNotFoundError(f"Dataset {dataset} not available")
        return await self.get_list(config.hips.legacy.dataset, config, logger)

    async def _build_hips_list(
        self, config: Config, dataset: str, logger: BoundLogger
    ) -> str:
        """Construct a HiPS list from the component properties files.

        Parameters
        ----------
        config
            Repertoire configuration.
        dataset
            Dataset for which to construct a HiPS list.
        logger
            Logger for error messages.

        Returns
        -------
        str
            HiPS list content.

        Raises
        ------
        HipsDatasetNotFoundError
            Raised if the requested dataset has no HiPS configuration.
        HipsWebError
            Raised if an error was encountered retrieving the underlying
            properties file.
        """
        if not config.token:
            raise HipsDatasetNotFoundError("HiPS lists not configured")
        if not config.hips or dataset not in config.hips.datasets:
            raise HipsDatasetNotFoundError(f"No HiPS dataset for {dataset}")
        if dataset not in config.available_datasets:
            raise HipsDatasetNotFoundError(f"Dataset {dataset} not available")
        template = Template(config.hips.source_template)
        context = {"base_hostname": config.base_hostname, "dataset": dataset}
        base_url = template.render(**context)

        # Retrieve the properties file for each underlying path, in the order
        # listed, and assemble them.
        entries = []
        token = config.token.get_secret_value()
        for path in config.hips.datasets[dataset].paths:
            url = base_url + "/" + path
            entries.append(await self._get_hips_list_entry(url, token, logger))

        # The HiPS list is the concatenation of all the adjusted properties
        # files, separated by blank lines.
        return "\n".join(entries)

    async def _get_hips_list_entry(
        self, url: str, token: str, logger: BoundLogger
    ) -> str:
        """Get one entry for a HiPS list file.

        Retrieve the properties metadata for one HiPS survey, add the
        ``hips_service_url`` entry, and return the results.

        Parameters
        ----------
        url
            URL of the HiPS survey.
        token
            Gafaelfawr token to use for authentication.
        logger
            Logger to use.

        Returns
        -------
        str
            Modified properties file, suitable for use as one entry in the
            HiPS list.

        Raises
        ------
        HipsWebError
            Raised if an error was encountered retrieving the underlying
            properties file.
        """
        try:
            r = await self._client.get(
                url + "/properties",
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()
        except HTTPError as e:
            logger.exception("Unable to get HiPS properties file", url=url)
            raise HipsWebError.from_exception(e) from e

        # Our HiPS surveys are relocatable so the properties file doesn't
        # contain the URL (hips_service_url). This is mandatory in the HiPS
        # list, so has to be added. Do so before hips_status.
        service_url = "{:25}= {}".format("hips_service_url", url)
        result = re.sub(
            "^hips_status",
            f"{service_url}\nhips_status",
            r.text,
            flags=re.MULTILINE,
        )
        if not result.endswith("\n"):
            result += "\n"
        return result


hips_list_dependency = HipsListDependency()
"""Caching dependency for generating HiPS lists."""
