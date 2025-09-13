"""Tests for the InfluxDB discovery client."""

from __future__ import annotations

import pytest
import respx
from httpx import Request, Response

from rubin.repertoire import DiscoveryClient

from ..support.constants import TEST_BASE_URL
from ..support.data import read_test_json


@pytest.mark.asyncio
async def test_databases(discovery_client: DiscoveryClient) -> None:
    output = read_test_json("output/phalanx")
    expected = list(output["influxdb_databases"].keys())
    assert await discovery_client.influxdb_databases() == expected


@pytest.mark.asyncio
async def test_connection_info(discovery_client: DiscoveryClient) -> None:
    client = discovery_client

    for database in ("idfdev_efd", "idfdev_metrics"):
        output = await client.get_influxdb_connection_info(database, "token")
        assert output
        output_json = output.model_dump(mode="json", exclude_none=True)
        assert output_json == read_test_json(f"output/{database}")

    assert await client.get_influxdb_connection_info("invalid", "t") is None


@pytest.mark.asyncio
async def test_authentication(respx_mock: respx.Router) -> None:
    result = read_test_json("output/idfdev_efd")
    discovery_url = f"{TEST_BASE_URL}repertoire/discovery"
    influxdb_url = f"{TEST_BASE_URL}repertoire/discovery/influxdb/idfdev_efd"
    token = "some-gafaelfawr-token"

    def check_request(request: Request) -> Response:
        assert request.headers["Authorization"] == f"Bearer {token}"
        return Response(200, json=result)

    discovery_response = Response(200, json=read_test_json("output/phalanx"))
    respx_mock.get(discovery_url).mock(return_value=discovery_response)
    respx_mock.get(influxdb_url).mock(side_effect=check_request)

    discovery = DiscoveryClient(base_url=f"{TEST_BASE_URL}repertoire")
    output = await discovery.get_influxdb_connection_info("idfdev_efd", token)
    assert output
    output_json = output.model_dump(mode="json", exclude_none=True)
    assert output_json == result
