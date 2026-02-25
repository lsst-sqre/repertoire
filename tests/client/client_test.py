"""Tests for the service discovery client."""

from datetime import timedelta
from unittest.mock import ANY

import pytest
import respx
from httpx import Response
from safir.testing.data import Data
from safir.testing.logging import parse_log_tuples
from structlog.stdlib import BoundLogger

from rubin.repertoire import DiscoveryClient, RepertoireWebError


@pytest.mark.asyncio
async def test_applications(data: Data, discovery: DiscoveryClient) -> None:
    output = data.read_json("output/phalanx")
    assert await discovery.applications() == output["applications"]


@pytest.mark.asyncio
async def test_datasets(data: Data, discovery: DiscoveryClient) -> None:
    output = data.read_json("output/phalanx")
    expected = sorted(output["datasets"].keys())
    assert await discovery.datasets() == expected


@pytest.mark.asyncio
async def test_butler_config_for(
    data: Data, discovery: DiscoveryClient
) -> None:
    output = data.read_json("output/phalanx")
    for dataset in output["datasets"]:
        result = await discovery.butler_config_for(dataset)
        assert result == output["datasets"][dataset].get("butler_config")
    assert await discovery.butler_config_for("unknown") is None


@pytest.mark.asyncio
async def test_butler_repositories(
    data: Data, discovery: DiscoveryClient
) -> None:
    output = data.read_json("output/phalanx")
    expected = {
        k: v["butler_config"]
        for k, v in output["datasets"].items()
        if v.get("butler_config") is not None
    }
    assert await discovery.butler_repositories() == expected


@pytest.mark.asyncio
async def test_environment_name(
    data: Data, discovery: DiscoveryClient
) -> None:
    output = data.read_json("output/phalanx")
    assert await discovery.environment_name() == output["environment_name"]


@pytest.mark.asyncio
async def test_url_for(data: Data, discovery: DiscoveryClient) -> None:
    output = data.read_json("output/phalanx")
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
async def test_versions_for(data: Data, discovery: DiscoveryClient) -> None:
    output = data.read_json("output/phalanx")
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
async def test_default_client(data: Data, respx_mock: respx.Router) -> None:
    output = data.read_json("output/phalanx")
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


@pytest.mark.asyncio
async def test_cache(data: Data, respx_mock: respx.Router) -> None:
    base_url = "https://api.example.com/repertoire"
    respx_mock.get(base_url + "/discovery").mock(return_value=Response(404))

    # Requesting discovery information with no cache when the service is down
    # should raise an exception.
    discovery = DiscoveryClient(base_url=base_url)
    with pytest.raises(RepertoireWebError):
        await discovery.applications()

    initial = data.read_json("output/phalanx")
    base_url = "https://api.example.com/repertoire"
    response = Response(200, json=initial)
    respx_mock.get(base_url + "/discovery").mock(return_value=response)

    discovery = DiscoveryClient(base_url=base_url)
    assert await discovery.applications() == initial["applications"]

    # Replace the discovery information with different information. The client
    # should not see any changes since the information is cached.
    new = data.read_json("output/minimal")
    response = Response(200, json=new)
    respx_mock.get(base_url + "/discovery").mock(return_value=response)
    assert await discovery.applications() == initial["applications"]

    # A new client will see the new information.
    discovery = DiscoveryClient(base_url=base_url)
    assert await discovery.applications() == []


@pytest.mark.asyncio
async def test_cache_timeout(data: Data, respx_mock: respx.Router) -> None:
    initial = data.read_json("output/phalanx")
    base_url = "https://api.example.com/repertoire"
    response = Response(200, json=initial)
    respx_mock.get(base_url + "/discovery").mock(return_value=response)

    timeout = timedelta(seconds=0)
    discovery = DiscoveryClient(base_url=base_url, cache_timeout=timeout)
    assert await discovery.applications() == initial["applications"]

    # Since the cache timeout is set to 0, replacing the output should produce
    # an immedate change in the results.
    new = data.read_json("output/minimal")
    response = Response(200, json=new)
    respx_mock.get(base_url + "/discovery").mock(return_value=response)
    assert await discovery.applications() == []


@pytest.mark.asyncio
async def test_cache_failure(
    *,
    data: Data,
    logger: BoundLogger,
    respx_mock: respx.Router,
    caplog: pytest.LogCaptureFixture,
) -> None:
    base_url = "https://api.example.com/repertoire"
    respx_mock.get(base_url + "/discovery").mock(return_value=Response(404))

    # Try retrieving information when Repertoire is down.
    discovery = DiscoveryClient(
        base_url=base_url, cache_timeout=timedelta(seconds=0), logger=logger
    )
    with pytest.raises(RepertoireWebError):
        await discovery.applications()

    # Configure with real data.
    output = data.read_json("output/phalanx")
    response = Response(200, json=output)
    respx_mock.get(base_url + "/discovery").mock(return_value=response)

    # Now, the client should immediately return real data.
    assert await discovery.applications() == output["applications"]

    # Make Repertoire return an error again. The client should return cached
    # data even though the cache has expired, but it should log a warning.
    caplog.clear()
    respx_mock.get(base_url + "/discovery").mock(return_value=Response(404))
    assert await discovery.applications() == output["applications"]
    seen = parse_log_tuples("test", caplog.record_tuples)
    assert seen == [
        {
            "error": ANY,
            "event": (
                "Failed to refresh service discovery information, returning"
                " cached data"
            ),
            "severity": "warning",
        }
    ]
