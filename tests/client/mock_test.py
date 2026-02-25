"""Test the client mocks."""

import pytest
import respx
from httpx import AsyncClient
from pydantic import HttpUrl
from safir.testing.data import Data

from rubin.repertoire import (
    Discovery,
    InternalService,
    RepertoireUrlError,
    Services,
    register_mock_discovery,
)


@pytest.mark.asyncio
async def test_register_model(respx_mock: respx.Router) -> None:
    results = Discovery(
        services=Services(
            internal={
                "foo": InternalService(url=HttpUrl("https://example.com/"))
            }
        )
    )
    expected = results.model_dump(mode="json", exclude_defaults=True)
    base_url = "https://example.com/repertoire"
    assert register_mock_discovery(respx_mock, results, base_url) == results
    async with AsyncClient() as client:
        r = await client.get(base_url + "/discovery")
        assert r.json() == expected


@pytest.mark.asyncio
async def test_register_json(data: Data, respx_mock: respx.Router) -> None:
    results = data.read_json("output/phalanx")
    base_url = "https://example.com/repertoire/"
    register_mock_discovery(respx_mock, results, base_url)
    async with AsyncClient() as client:
        r = await client.get(base_url.rstrip("/") + "/discovery")
        assert r.json() == results


@pytest.mark.asyncio
async def test_register_path(data: Data, respx_mock: respx.Router) -> None:
    results_path = data.path("output/phalanx.json")
    results = data.read_json("output/phalanx")
    base_url = "https://example.com/repertoire"
    register_mock_discovery(respx_mock, results_path, base_url)
    async with AsyncClient() as client:
        r = await client.get(base_url + "/discovery")
        assert r.json() == results


@pytest.mark.asyncio
async def test_register_env(
    data: Data, respx_mock: respx.Router, monkeypatch: pytest.MonkeyPatch
) -> None:
    results_path = data.path("output/phalanx.json")
    base_url = "https://example.com/repertoire"

    # If base_url is not provided, REPERTOIRE_BASE_URL must be set.
    with pytest.raises(RepertoireUrlError):
        register_mock_discovery(respx_mock, results_path)

    monkeypatch.setenv("REPERTOIRE_BASE_URL", base_url)
    register_mock_discovery(respx_mock, results_path)
    async with AsyncClient() as client:
        r = await client.get(base_url + "/discovery")
        data.assert_json_matches(r.json(), "output/phalanx")
