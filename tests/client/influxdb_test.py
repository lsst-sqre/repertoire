"""Tests for the InfluxDB discovery client."""

import pytest
import respx
from httpx import Request, Response
from safir.testing.data import Data

from rubin.repertoire import DiscoveryClient

from ..support.constants import TEST_BASE_URL


@pytest.mark.asyncio
async def test_databases(data: Data, discovery: DiscoveryClient) -> None:
    output = data.read_json("output/phalanx")
    expected = list(output["influxdb_databases"].keys())
    assert await discovery.influxdb_databases() == expected


@pytest.mark.asyncio
async def test_connection_info(data: Data, discovery: DiscoveryClient) -> None:
    for database in ("idfdev_efd", "idfdev_metrics"):
        output = await discovery.influxdb_connection_info(database)
        assert output
        data.assert_pydantic_matches(
            output, f"output/{database}", exclude_defaults=True
        )
    assert await discovery.influxdb_connection_info("invalid") is None


@pytest.mark.asyncio
async def test_credentials(data: Data, discovery: DiscoveryClient) -> None:
    for database in ("idfdev_efd", "idfdev_metrics"):
        output = await discovery.influxdb_credentials(database, "token")
        assert output
        data.assert_pydantic_matches(
            output, f"output/{database}-creds", exclude_defaults=True
        )
    assert await discovery.influxdb_credentials("invalid", "token") is None


@pytest.mark.asyncio
async def test_authentication(data: Data, respx_mock: respx.Router) -> None:
    result = data.read_json("output/idfdev_efd-creds")
    discovery_url = f"{TEST_BASE_URL}repertoire/discovery"
    influxdb_url = f"{TEST_BASE_URL}repertoire/discovery/influxdb/idfdev_efd"
    token = "some-gafaelfawr-token"

    def check_request(request: Request) -> Response:
        assert request.headers["Authorization"] == f"Bearer {token}"
        return Response(200, json=result)

    discovery_response = Response(200, json=data.read_json("output/phalanx"))
    respx_mock.get(discovery_url).mock(return_value=discovery_response)
    respx_mock.get(influxdb_url).mock(side_effect=check_request)

    discovery = DiscoveryClient(base_url=f"{TEST_BASE_URL}repertoire")
    output = await discovery.influxdb_credentials("idfdev_efd", token)
    assert output
    data.assert_pydantic_matches(
        output, "output/idfdev_efd-creds", exclude_defaults=True
    )
