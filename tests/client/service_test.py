"""Tests for the service discovery client."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from rubin.repertoire import DiscoveryClient

from ..support.data import read_test_json


@pytest.mark.asyncio
async def test_applications(discovery: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    assert await discovery.applications() == output["applications"]


@pytest.mark.asyncio
async def test_datasets(discovery: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    expected = sorted(output["datasets"].keys())
    assert await discovery.datasets() == expected


@pytest.mark.asyncio
async def test_butler_config_for(discovery: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    for dataset in output["datasets"]:
        result = await discovery.butler_config_for(dataset)
        assert result == output["datasets"][dataset].get("butler_config")
    assert await discovery.butler_config_for("unknown") is None


@pytest.mark.asyncio
async def test_butler_repositories(discovery: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    expected = {
        k: v["butler_config"]
        for k, v in output["datasets"].items()
        if v.get("butler_config") is not None
    }
    assert await discovery.butler_repositories() == expected


@pytest.mark.asyncio
async def test_environment_name(discovery: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    assert await discovery.environment_name() == output["environment_name"]


@pytest.mark.asyncio
async def test_url_for(discovery: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    services = output["services"]

    for service, info in services["internal"].items():
        assert await discovery.url_for_internal(service) == info["url"]
    assert await discovery.url_for_internal("unknown") is None

    for service, info in services["ui"].items():
        assert await discovery.url_for_ui(service) == info["url"]
    assert await discovery.url_for_ui("unknown") is None

    for dataset, mapping in output["datasets"].items():
        for service, info in mapping["services"].items():
            result = await discovery.url_for_data(service, dataset)
            assert result == info["url"]
        assert await discovery.url_for_data(service, "unknown") is None
    assert await discovery.url_for_data("unknown", dataset) is None


@pytest.mark.asyncio
async def test_versions_for(discovery: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    services = output["services"]

    for dataset, mapping in output["datasets"].items():
        for service, info in mapping["services"].items():
            result = await discovery.versions_for_data(service, dataset)
            versions = info.get("versions", {})
            assert result == sorted(versions.keys())
            for version, version_info in versions.items():
                url = await discovery.url_for_data(
                    service, dataset, version=version
                )
                assert url == version_info["url"]
            url = await discovery.url_for_data(service, dataset, version="bad")
            assert url is None
        url = await discovery.url_for_data(service, "bad", version="bad")
        assert url is None
    assert await discovery.url_for_data("bad", "bad", version="bad") is None

    for service, info in services["internal"].items():
        result = await discovery.versions_for_internal(service)
        versions = info.get("versions")
        if not versions:
            assert result == []
            continue
        assert result == sorted(versions.keys())
        for version, version_info in versions.items():
            url = await discovery.url_for_internal(service, version=version)
            assert url == version_info["url"]
        assert await discovery.url_for_internal(service, version="bad") is None
    assert await discovery.url_for_internal("bad", version="bad") is None


@pytest.mark.asyncio
async def test_default_client(respx_mock: respx.Router) -> None:
    output = read_test_json("output/phalanx")
    base_url = "https://api.example.com/repertoire"
    response = Response(200, json=output)
    respx_mock.get(base_url + "/discovery").mock(return_value=response)

    discovery = DiscoveryClient(base_url=base_url)
    assert await discovery.applications() == output["applications"]
    await discovery.aclose()

    # Slashes tend to get accidentally added to the ends of paths, so test
    # that the client is robust.
    discovery = DiscoveryClient(base_url=base_url + "/")
    assert await discovery.applications() == output["applications"]
    await discovery.aclose()
