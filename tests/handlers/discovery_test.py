"""Tests for the repertoire.handlers.discovery module and routes."""

import pytest
from httpx import AsyncClient
from safir.metrics import MockEventPublisher
from safir.testing.data import Data

from repertoire.dependencies.config import config_dependency
from repertoire.dependencies.events import events_dependency

from ..support.constants import TEST_BASE_URL


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
@pytest.mark.parametrize("app", ["minimal"], indirect=True)
async def test_minimal(data: Data, client: AsyncClient) -> None:
    r = await client.get("/repertoire/discovery")
    assert r.status_code == 200, f"error body: {r.text}"
    data.assert_json_matches(r.json(), "output/minimal")


@pytest.mark.asyncio
async def test_get_discovery(data: Data, client: AsyncClient) -> None:
    r = await client.get("/repertoire/discovery")
    assert r.status_code == 200, f"error body: {r.text}"
    data.assert_json_matches(r.json(), "output/phalanx")


@pytest.mark.asyncio
async def test_get_influxdb(data: Data, client: AsyncClient) -> None:
    r = await client.get("/repertoire/discovery")
    assert r.status_code == 200, f"error body: {r.text}"

    seen = r.json()["influxdb_databases"]["idfdev_efd"]
    url = seen["credentials_url"]
    del seen["credentials_url"]
    data.assert_json_matches(seen, "output/idfdev_efd")
    assert url == f"{TEST_BASE_URL}repertoire/discovery/influxdb/idfdev_efd"
    r = await client.get(url, headers={"X-Auth-Request-User": "some-user"})
    assert r.status_code == 200, f"error body: {r.text}"
    data.assert_json_matches(r.json(), "output/idfdev_efd-creds")

    r = await client.get(
        f"{TEST_BASE_URL}repertoire/discovery/influxdb/bogus",
        headers={"X-Auth-Request-User": "some-user"},
    )
    assert r.status_code == 404

    publisher = (await events_dependency()).influx_creds
    assert isinstance(publisher, MockEventPublisher)
    publisher.published.assert_published_all(
        [{"username": "some-user", "label": "idfdev_efd"}]
    )
