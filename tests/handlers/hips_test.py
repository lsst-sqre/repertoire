"""Tests for the repertoire.handlers.hips module and routes."""

import pytest
from httpx import AsyncClient

from ..support.data import read_test_file


@pytest.mark.asyncio
async def test_list(client: AsyncClient) -> None:
    r = await client.get("/api/hips/v2/dp1/list")
    assert r.status_code == 200, f"error body: {r.text}"
    assert r.text == read_test_file("output/hips-dp1-list")
    r = await client.get("/api/hips/v2/dp02/list")
    assert r.status_code == 200, f"error body: {r.text}"
    r = await client.get("/api/hips/v2/dp03/list")
    assert r.status_code == 404
    r = await client.get("/api/hips/v2/unknown/list")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_legacy(client: AsyncClient) -> None:
    r = await client.get("/api/hips/list")
    assert r.status_code == 200, f"error body: {r.text}"
    assert r.text == read_test_file("output/hips-dp1-list")


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["no-legacy"], indirect=True)
async def test_no_legacy(client: AsyncClient) -> None:
    r = await client.get("/api/hips/list")
    assert r.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["no-hips"], indirect=True)
async def test_no_hips(client: AsyncClient) -> None:
    r = await client.get("/api/hips/list")
    assert r.status_code == 404
    r = await client.get("/api/hips/v2/dp1/list")
    assert r.status_code == 404
