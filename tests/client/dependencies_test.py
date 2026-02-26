"""Tests for Repertoire client FastAPI dependencies."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

import pytest
import respx
from asgi_lifespan import LifespanManager
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from safir.dependencies.http_client import http_client_dependency
from safir.testing.data import Data
from safir.testing.logging import parse_log_tuples
from structlog.stdlib import BoundLogger

from rubin.repertoire import (
    DiscoveryClient,
    discovery_dependency,
    register_mock_discovery,
)


@pytest.mark.asyncio
async def test_dependency(
    *,
    data: Data,
    logger: BoundLogger,
    respx_mock: respx.Router,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached_client = None
    output = data.read_json("output/phalanx")
    monkeypatch.setenv("REPERTOIRE_BASE_URL", "https://example.com/repertoire")
    register_mock_discovery(respx_mock, output)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        yield
        await http_client_dependency.aclose()

    app = FastAPI(lifespan=lifespan)
    discovery_dependency.initialize(logger)

    @app.get("/")
    async def get_root(
        discovery: Annotated[DiscoveryClient, Depends(discovery_dependency)],
    ) -> None:
        nonlocal cached_client
        if cached_client is None:
            cached_client = discovery
        assert discovery == cached_client
        assert await discovery.applications() == output["applications"]

    caplog.clear()
    async with LifespanManager(app):
        async with AsyncClient(
            base_url="https://example.com/", transport=ASGITransport(app=app)
        ) as client:
            r = await client.get("/")
            assert r.status_code == 200
            r = await client.get("/")
            assert r.status_code == 200

    # Check that the correct logger was used and the fetch of data was logged.
    seen = parse_log_tuples("test", caplog.record_tuples)
    assert seen == [
        {
            "event": "Retrieved service discovery information",
            "timeout": 300.0,
            "severity": "debug",
        }
    ]

    # When the HTTPX client dependency is shut down and recreated, this should
    # result in a new Gafaelfawr client. Otherwise, the Gafaelfawr client
    # would try to use the closed HTTPX client.
    old_client = cached_client
    cached_client = None
    async with LifespanManager(app):
        async with AsyncClient(
            base_url="https://example.com/", transport=ASGITransport(app=app)
        ) as client:
            r = await client.get("/")
            assert r.status_code == 200
            assert cached_client != old_client
