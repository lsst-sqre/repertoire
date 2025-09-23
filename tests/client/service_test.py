"""Tests for the service discovery client."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from rubin.repertoire import DiscoveryClient

from ..support.data import read_test_json


@pytest.mark.asyncio
async def test_applications(discovery_client: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    assert await discovery_client.applications() == output["applications"]


@pytest.mark.asyncio
async def test_datasets(discovery_client: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    expected = sorted(output["datasets"].keys())
    assert await discovery_client.datasets() == expected


@pytest.mark.asyncio
async def test_butler_config_for(discovery_client: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    for dataset in output["datasets"]:
        result = await discovery_client.butler_config_for(dataset)
        assert result == output["datasets"][dataset].get("butler_config")
    assert await discovery_client.butler_config_for("unknown") is None


@pytest.mark.asyncio
async def test_butler_repositories(discovery_client: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    expected = {
        k: v["butler_config"]
        for k, v in output["datasets"].items()
        if v.get("butler_config") is not None
    }
    assert await discovery_client.butler_repositories() == expected


@pytest.mark.asyncio
async def test_url_for(discovery_client: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    services = output["services"]

    for service, info in services["internal"].items():
        url = info["url"]
        assert await discovery_client.url_for_internal_service(service) == url
    assert await discovery_client.url_for_internal_service("unknown") is None

    for service, info in services["ui"].items():
        url = info["url"]
        assert await discovery_client.url_for_ui_service(service) == url
    assert await discovery_client.url_for_ui_service("unknown") is None

    client = discovery_client
    for service, mapping in services["data"].items():
        for dataset, info in mapping.items():
            result = await client.url_for_data_service(service, dataset)
            assert result == info["url"]
        assert await client.url_for_data_service(service, "unknown") is None
    assert await client.url_for_data_service("unknown", dataset) is None


@pytest.mark.asyncio
async def test_default_client(respx_mock: respx.Router) -> None:
    output = read_test_json("output/phalanx")
    base_url = "https://api.example.com/repertoire"
    response = Response(200, json=output)
    respx_mock.get(base_url + "/discovery").mock(return_value=response)

    discovery = DiscoveryClient(base_url=base_url)
    assert await discovery.applications() == output["applications"]

    # Slashes tend to get accidentally added to the ends of paths, so test
    # that the client is robust.
    discovery = DiscoveryClient(base_url=base_url + "/")
    assert await discovery.applications() == output["applications"]
