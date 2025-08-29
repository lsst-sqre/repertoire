"""Tests for the repertoire.handlers.external module and routes."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from repertoire.dependencies.config import config_dependency

from ..support.data import data_path, read_test_json


@pytest.mark.asyncio
async def test_get_index(client: AsyncClient) -> None:
    r = await client.get("/repertoire/")
    assert r.status_code == 200
    data = r.json()
    metadata = data["metadata"]
    assert metadata["name"] == config_dependency.config().name
    assert isinstance(metadata["version"], str)
    assert isinstance(metadata["description"], str)
    assert isinstance(metadata["repository_url"], str)
    assert isinstance(metadata["documentation_url"], str)


@pytest.mark.asyncio
async def test_get_discovery(client: AsyncClient) -> None:
    config_dependency.set_config_path(data_path("config/phalanx.yaml"))
    r = await client.get("/repertoire/discovery")
    assert r.status_code == 200, f"error body: {r.text}"
    assert r.json() == read_test_json("output/phalanx")
