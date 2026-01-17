"""Test the client mocks."""

from __future__ import annotations

import pytest
import respx
from httpx import AsyncClient
from pydantic import HttpUrl

from rubin.repertoire import (
    Discovery,
    InternalService,
    RepertoireUrlError,
    Services,
    register_mock_discovery,
)

from ..support.data import data_path, read_test_json


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
async def test_register_json(respx_mock: respx.Router) -> None:
    results = read_test_json("output/phalanx")
    model = Discovery.model_validate(results)
    base_url = "https://example.com/repertoire/"
    assert register_mock_discovery(respx_mock, results, base_url) == model
    async with AsyncClient() as client:
        r = await client.get(base_url.rstrip("/") + "/discovery")
        assert r.json() == results


@pytest.mark.asyncio
async def test_register_path(respx_mock: respx.Router) -> None:
    results_path = data_path("output/phalanx.json")
    results_json = read_test_json("output/phalanx")
    model = Discovery.model_validate(results_json)
    base_url = "https://example.com/repertoire"
    assert register_mock_discovery(respx_mock, results_path, base_url) == model
    async with AsyncClient() as client:
        r = await client.get(base_url + "/discovery")
        assert r.json() == results_json


@pytest.mark.asyncio
async def test_register_env(
    respx_mock: respx.Router, monkeypatch: pytest.MonkeyPatch
) -> None:
    results_path = data_path("output/phalanx.json")
    base_url = "https://example.com/repertoire"

    # If base_url is not provided, REPERTOIRE_BASE_URL must be set.
    with pytest.raises(RepertoireUrlError):
        register_mock_discovery(respx_mock, results_path)

    monkeypatch.setenv("REPERTOIRE_BASE_URL", base_url)
    register_mock_discovery(respx_mock, results_path)
    async with AsyncClient() as client:
        r = await client.get(base_url + "/discovery")
        assert r.json() == read_test_json("output/phalanx")
