"""Tests for the service discovery client."""

from __future__ import annotations

import pytest
import respx
from httpx import AsyncClient, Response

from repertoire.dependencies.config import config_dependency
from rubin.repertoire import DiscoveryClient

from ..support.constants import TEST_BASE_URL
from ..support.data import data_path, read_test_json


@pytest.fixture
def discovery(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> DiscoveryClient:
    config_dependency.set_config_path(data_path("config/phalanx.yaml"))
    repertoire_url = TEST_BASE_URL.rstrip("/") + "/repertoire"
    monkeypatch.setenv("REPERTOIRE_BASE_URL", repertoire_url)
    return DiscoveryClient(client)


@pytest.mark.asyncio
async def test_applications(discovery: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    assert await discovery.applications() == output["applications"]


@pytest.mark.asyncio
async def test_datasets(discovery: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    expected = sorted(d["name"] for d in output["datasets"])
    assert await discovery.datasets() == expected


@pytest.mark.asyncio
async def test_butler_config_for(discovery: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    for dataset in output["datasets"]:
        result = await discovery.butler_config_for(dataset["name"])
        assert result == dataset.get("butler_config")
    assert await discovery.butler_config_for("unknown") is None


@pytest.mark.asyncio
async def test_butler_repositories(discovery: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    expected = {
        d["name"]: d["butler_config"]
        for d in output["datasets"]
        if d.get("butler_config") is not None
    }
    assert await discovery.butler_repositories() == expected


@pytest.mark.asyncio
async def test_url_for(discovery: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    urls = output["urls"]

    for service, url in urls["internal"].items():
        assert await discovery.url_for_internal_service(service) == url
    assert await discovery.url_for_internal_service("unknown") is None

    for service, url in urls["ui"].items():
        assert await discovery.url_for_ui_service(service) == url
    assert await discovery.url_for_ui_service("unknown") is None

    for service, mapping in urls["data"].items():
        for dataset, url in mapping.items():
            result = await discovery.url_for_data_service(service, dataset)
            assert result == url
        assert await discovery.url_for_data_service(service, "unknown") is None
    assert await discovery.url_for_data_service("unknown", dataset) is None


@pytest.mark.asyncio
async def test_default_client(respx_mock: respx.Router) -> None:
    output = read_test_json("output/phalanx")
    discovery_url = "https://api.example.com/repertoire/discovery"
    response = Response(200, json=output)
    respx_mock.get(discovery_url).mock(return_value=response)

    discovery = DiscoveryClient(base_url="https://api.example.com/repertoire")
    assert await discovery.applications() == output["applications"]

    discovery = DiscoveryClient(base_url="https://api.example.com/repertoire/")
    assert await discovery.applications() == output["applications"]
