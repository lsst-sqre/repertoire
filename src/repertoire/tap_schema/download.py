"""Schema download and extraction utilities.

Download schema archives from multiple sources
(GCS, HTTP/HTTPS) and extract them to a working directory.
"""

from __future__ import annotations

import tarfile
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx
from google.cloud import storage

if TYPE_CHECKING:
    from structlog.stdlib import BoundLogger

__all__ = ["download_schemas"]

_DOWNLOAD_CHUNK_SIZE = 64 * 1024
"""Chunk size for HTTP downloads."""


async def _download_from_gcs(
    url: str,
    destination: Path,
    logger: BoundLogger,
) -> None:
    """Download from Google Cloud Storage.

    Parameters
    ----------
    url
        GCS URL.
    destination
        Local path where file should be saved.
    logger
        Structured logger.

    Raises
    ------
    RuntimeError
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
    except Exception as e:
        logger.exception("GCS download failed", url=url)
        raise RuntimeError(
            f"Failed to download from GCS: {e}. "
            f"Bucket: {bucket_name}, Blob: {blob_path}. "
            f"Verify bucket exists and credentials have read permissions."
        ) from e


async def _download_from_http(
    url: str,
    destination: Path,
    logger: BoundLogger,
) -> None:
    """Download from HTTP/HTTPS using httpx.

    Parameters
    ----------
    url
        HTTP/HTTPS URL.
    destination
        Local path where file should be saved.
    logger
        Structured logger.

    Raises
    ------
    RuntimeError
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

    except httpx.HTTPError as e:
        logger.exception("HTTP download failed", error=str(e), url=url)
        raise RuntimeError(f"Failed to download via HTTP: {e}") from e


def _extract_tarball(
    archive_path: Path,
    extract_dir: Path,
    logger: BoundLogger,
) -> None:
    """Extract a tar.gz archive.

    Parameters
    ----------
    archive_path
        Path to the tar.gz archive.
    extract_dir
        Directory where files should be extracted.
    logger
        Structured logger.

    Raises
    ------
    RuntimeError
        If extraction fails.
    """
    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=extract_dir, filter="data")
    except tarfile.TarError as e:
        logger.exception("Extraction failed", error=str(e))
        raise RuntimeError(f"Failed to extract archive: {e}") from e


async def download_schemas(
    schema_version: str,
    source_url_template: str,
    work_dir: Path,
    logger: BoundLogger,
) -> Path:
    """Download schemas and return path to YAML directory.

    Parameters
    ----------
    schema_version
        Version tag.
    source_url_template
        URL template with {version} placeholder. Examples:
        - "gs://sdm-schemas/{version}.tar.gz"
        - "https://github.com/lsst/sdm_schemas/archive/refs/tags/{version}.tar.gz"
    work_dir
        Working directory for extraction.
    logger
        Structured logger.

    Returns
    -------
    Path
        Path to the directory containing YAML schema files.

    Raises
    ------
    ValueError
        If URL scheme is not supported.
    RuntimeError
        If extraction fails or schema directory not found.
    """
    schema_dir = work_dir / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)

    url = source_url_template.format(version=schema_version)
    parsed = urlparse(url)
    archive_path = schema_dir / f"{schema_version}.tar.gz"

    if parsed.scheme == "gs":
        await _download_from_gcs(url, archive_path, logger)
    elif parsed.scheme in ("http", "https"):
        await _download_from_http(url, archive_path, logger)
    else:
        raise ValueError(
            f"Unsupported URL scheme: {parsed.scheme}. "
            f"Supported schemes: gs, http, https"
        )

    _extract_tarball(archive_path, schema_dir, logger)

    extracted_dirs = [d for d in schema_dir.iterdir() if d.is_dir()]
    if not extracted_dirs:
        raise RuntimeError("No directories found after extraction")

    top_dir = extracted_dirs[0]
    yaml_dir = top_dir / "python" / "lsst" / "sdm" / "schemas"

    if not yaml_dir.exists():
        raise RuntimeError(
            f"Schema directory not found: {yaml_dir}. "
            f"Expected structure: <archive>/python/lsst/sdm/schemas/ "
            f"Found: {top_dir}"
        )

    yaml_files = list(yaml_dir.glob("*.yaml"))
    if not yaml_files:
        raise RuntimeError(
            f"No YAML files found in {yaml_dir}. "
            f"Schema directory exists but contains no schema definitions."
        )

    logger.info(
        "Schemas downloaded successfully",
        url=url,
        schema_version=schema_version,
    )
    return yaml_dir
