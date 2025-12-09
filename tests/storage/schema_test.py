"""Tests for schema download functionality."""

from __future__ import annotations

import tarfile
from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import structlog
from structlog.stdlib import BoundLogger

from repertoire.exceptions import TAPSchemaDownloadError
from repertoire.storage.tap_schema import TAPSchemaStorage


@pytest.fixture
def logger() -> BoundLogger:
    """Provide a test logger."""
    return structlog.get_logger("test")


@pytest.fixture
def storage(logger: BoundLogger) -> TAPSchemaStorage:
    """Provide a test storage instance."""
    return TAPSchemaStorage(logger)


@pytest.mark.asyncio
async def test_download_schemas_http_success(
    tmp_path: Path,
    storage: TAPSchemaStorage,
) -> None:
    archive_path = tmp_path / "schemas.tar.gz"
    schema_dir = tmp_path / "sdm_schemas-w.2025.43"
    yaml_dir = schema_dir / "python" / "lsst" / "sdm" / "schemas"
    yaml_dir.mkdir(parents=True)

    (yaml_dir / "test_schema.yaml").write_text("name: test_schema")

    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(schema_dir, arcname=schema_dir.name)

    mock_response = MagicMock()
    mock_response.headers = {
        "content-length": str(archive_path.stat().st_size)
    }

    async def mock_aiter_bytes(chunk_size: int) -> AsyncIterator[bytes]:
        with Path.open(archive_path, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk

    mock_response.aiter_bytes = mock_aiter_bytes
    mock_response.raise_for_status = MagicMock()

    mock_stream = MagicMock()
    mock_stream.__aenter__ = AsyncMock(return_value=mock_response)
    mock_stream.__aexit__ = AsyncMock()

    mock_client = MagicMock()
    mock_client.stream = MagicMock(return_value=mock_stream)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()

    with patch(
        "repertoire.storage.tap_schema.httpx.AsyncClient",
        return_value=mock_client,
    ):
        result = await storage.download_and_extract(
            schema_version="w.2025.43",
            source_url_template="https://example.com/{version}.tar.gz",
            work_dir=tmp_path / "work",
        )

    assert result.exists()
    assert result.name == "schemas"
    assert (result / "test_schema.yaml").exists()


@pytest.mark.asyncio
async def test_download_schemas_http_failure(
    tmp_path: Path,
    storage: TAPSchemaStorage,
) -> None:
    with patch(
        "repertoire.storage.tap_schema.TAPSchemaStorage._download_from_http",
        side_effect=TAPSchemaDownloadError(
            "Failed to download via HTTP: Connection failed",
            url="https://example.com/v1.0.tar.gz",
            schema_version="w.2025.43",
        ),
    ):
        with pytest.raises(
            TAPSchemaDownloadError, match="Failed to download via HTTP"
        ):
            await storage.download_and_extract(
                schema_version="w.2025.43",
                source_url_template="https://example.com/{version}.tar.gz",
                work_dir=tmp_path,
            )


@pytest.mark.asyncio
async def test_download_schemas_invalid_scheme(
    tmp_path: Path,
    storage: TAPSchemaStorage,
) -> None:
    with pytest.raises(ValueError, match="Unsupported URL scheme: ftp"):
        await storage.download_and_extract(
            schema_version="w.2025.43",
            source_url_template="ftp://example.com/{version}.tar.gz",
            work_dir=tmp_path,
        )
