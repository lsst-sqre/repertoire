"""Tests for Repertoire client FastAPI dependencies."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

import pytest
import respx
from asgi_lifespan import LifespanManager
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from safir.dependencies.http_client import http_client_dependency

from rubin.repertoire import (
    DiscoveryClient,
    discovery_dependency,
    register_mock_discovery,
)

from ..support.data import read_test_json


@pytest.mark.asyncio
async def test_dependency(
    respx_mock: respx.Router, monkeypatch: pytest.MonkeyPatch
) -> None:
    cached_client = None
    output = read_test_json("output/phalanx")
    monkeypatch.setenv("REPERTOIRE_BASE_URL", "https://example.com/repertoire")
    register_mock_discovery(respx_mock, output)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        yield
        await http_client_dependency.aclose()

    app = FastAPI(lifespan=lifespan)

    @app.get("/")
    async def get_root(
        discovery: Annotated[DiscoveryClient, Depends(discovery_dependency)],
    ) -> None:
        nonlocal cached_client
        if cached_client is None:
            cached_client = discovery
        assert discovery == cached_client
        assert await discovery.applications() == output["applications"]

    async with LifespanManager(app):
        async with AsyncClient(
            base_url="https://example.com/", transport=ASGITransport(app=app)
        ) as client:
            r = await client.get("/")
            assert r.status_code == 200
            r = await client.get("/")
            assert r.status_code == 200
