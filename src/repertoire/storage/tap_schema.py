"""Storage layer for schema download and extraction.

This module is responsible for downloading the schema archives from multiple
sources (GCS, HTTP/HTTPS) and extracting them to a working directory.
"""

from __future__ import annotations

import tarfile
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx
from google.cloud import storage

from repertoire.exceptions import (
    TAPSchemaDirectoryError,
    TAPSchemaDownloadError,
    TAPSchemaExtractionError,
)

if TYPE_CHECKING:
    from structlog.stdlib import BoundLogger

__all__ = ["TAPSchemaStorage"]

_DOWNLOAD_CHUNK_SIZE = 64 * 1024
"""Chunk size for HTTP downloads."""


class TAPSchemaStorage:
    """Storage layer for TAP_SCHEMA schema files.

    This class handles downloading schema files from GCS or HTTP/HTTPS,
    extracting them and validating the directory structure.

    Parameters
    ----------
    logger
        Logger for debug messages and errors.
    """

    def __init__(self, logger: BoundLogger) -> None:
        self._logger = logger

    async def download_and_extract(
        self,
        schema_version: str,
        source_url_template: str,
        work_dir: Path,
    ) -> Path:
        """Download and extract schema archive.

        Downloads a schema archive from either GCS or HTTP/HTTPS extracts it,
        validates the directory and returns the path to the schema files.

        Parameters
        ----------
        schema_version
            Version of the schema to download.
        source_url_template
            URL template with {version} placeholder. Examples:
            - "gs://sdm-schemas/{version}.tar.gz"
            - "https://github.com/lsst/sdm_schemas/archive/refs/tags/{version}.tar.gz"
        work_dir
            Working directory for extraction.

        Returns
        -------
        Path
            Path to the directory containing YAML schema files.

        Raises
        ------
        SchemaDownloadError
            If download fails.
        SchemaExtractionError
            If extraction fails.
        SchemaDirectoryError
            If the schema directory structure is invalid.
        ValueError
            If URL scheme is not supported.
        """
        schema_dir = work_dir / "schemas"
        schema_dir.mkdir(parents=True, exist_ok=True)

        url = source_url_template.format(version=schema_version)
        parsed = urlparse(url)
        archive_path = schema_dir / f"{schema_version}.tar.gz"

        if parsed.scheme == "gs":
            await self._download_from_gcs(url, archive_path, schema_version)
        elif parsed.scheme in ("http", "https"):
            await self._download_from_http(url, archive_path, schema_version)
        else:
            raise ValueError(
                f"Unsupported URL scheme: {parsed.scheme}. "
                f"Supported schemes: gs, http, https"
            )

        self._extract_tarball(archive_path, schema_dir)
        yaml_dir = self._locate_schema_directory(schema_dir)

        self._logger.debug(
            "Schemas downloaded and extracted successfully",
            url=url,
            schema_version=schema_version,
            schema_path=str(yaml_dir),
        )
        return yaml_dir

    async def _download_from_gcs(
        self,
        url: str,
        destination: Path,
        schema_version: str,
    ) -> None:
        """Download file from GCS.

        Parameters
        ----------
        url
            GCS URL (gs://bucket/path format).
        destination
            Local path where file should be saved.

        Raises
        ------
        TAPSchemaDownloadError
            If download fails.
        """
        bucket_name = ""
        blob_path = ""

        try:
            parsed = urlparse(url)
            bucket_name = parsed.netloc
            blob_path = parsed.path.lstrip("/")

            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_path)

            blob.download_to_filename(str(destination))

            self._logger.info(
                "Downloaded schema from GCS",
                bucket=bucket_name,
                blob=blob_path,
                destination=str(destination),
            )
        except Exception as e:
            self._logger.exception(
                "GCS download failed",
                url=url,
                bucket=bucket_name,
                blob=blob_path,
            )
            raise TAPSchemaDownloadError(
                f"Failed to download from GCS: {e}",
                url=url,
                schema_version=schema_version,
            ) from e

    async def _download_from_http(
        self,
        url: str,
        destination: Path,
        schema_version: str,
    ) -> None:
        """Download file from HTTP or HTTPS.

        Parameters
        ----------
        url
            HTTP or HTTPS URL.
        destination
            Local path where file should be saved.

        Raises
        ------
        TAPSchemaDownloadError
            If download fails.
        """
        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=300.0
            ) as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    with destination.open("wb") as f:
                        downloaded = 0
                        async for chunk in response.aiter_bytes(
                            chunk_size=_DOWNLOAD_CHUNK_SIZE
                        ):
                            f.write(chunk)
                            downloaded += len(chunk)

            self._logger.debug(
                "Downloaded schema from HTTP",
                url=url,
                destination=str(destination),
                bytes_downloaded=downloaded,
            )

        except httpx.HTTPError as e:
            raise TAPSchemaDownloadError(
                f"Failed to download via HTTP: {e}",
                url=url,
                schema_version=schema_version,
            ) from e

    def _extract_tarball(
        self,
        archive_path: Path,
        extract_dir: Path,
    ) -> None:
        """Extract a tar.gz archive.

        Parameters
        ----------
        archive_path
            Path to the tar.gz archive.
        extract_dir
            Directory where files should be extracted.

        Raises
        ------
        TAPSchemaExtractionError
            If extraction fails.
        """
        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(path=extract_dir, filter="data")

            self._logger.debug(
                "Extracted schema archive",
                archive=str(archive_path),
                extract_dir=str(extract_dir),
            )
        except tarfile.TarError as e:
            self._logger.exception(
                "Archive extraction failed",
                archive=str(archive_path),
            )
            raise TAPSchemaExtractionError(
                f"Failed to extract archive: {e}",
                archive_path=str(archive_path),
            ) from e

    def _locate_schema_directory(self, schema_dir: Path) -> Path:
        """Locate YAML schema directory in extracted archive.

        Validates that the extracted archive contains the expected
        structure and schema files.

        Parameters
        ----------
        schema_dir
            Root directory of extracted archive.

        Returns
        -------
        Path
            Path to YAML schema files.

        Raises
        ------
        TAPSchemaDirectoryError
            If schema directory structure is invalid or no YAML files found.
        """
        extracted_dirs = [d for d in schema_dir.iterdir() if d.is_dir()]
        if not extracted_dirs:
            raise TAPSchemaDirectoryError(
                "No directories found after extraction"
            )

        top_dir = extracted_dirs[0]
        yaml_dir = top_dir / "python" / "lsst" / "sdm" / "schemas"

        if not yaml_dir.exists():
            raise TAPSchemaDirectoryError(
                f"Schema directory not found: {yaml_dir}",
                schema_dir=str(yaml_dir),
            )

        yaml_files = list(yaml_dir.glob("*.yaml"))
        if not yaml_files:
            raise TAPSchemaDirectoryError(
                f"No YAML files found in {yaml_dir}",
                schema_dir=str(yaml_dir),
            )

        self._logger.debug(
            "Located schema directory",
            schema_dir=str(yaml_dir),
            file_count=len(yaml_files),
        )
        return yaml_dir
