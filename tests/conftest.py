"""Test fixtures for Repertoire tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from repertoire.dependencies.config import config_dependency
from repertoire.main import create_app
from rubin.repertoire import DiscoveryClient

from .support.constants import TEST_BASE_URL
from .support.data import data_path


@pytest_asyncio.fixture
async def app() -> AsyncGenerator[FastAPI]:
    """Return a configured test application.

    Wraps the application in a lifespan manager so that startup and shutdown
    events are sent during test execution.
    """
    config_dependency.set_config_path(data_path("config/minimal.yaml"))
    app = create_app(secrets_root=data_path("secrets"))
    async with LifespanManager(app):
        yield app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    """Return an ``httpx.AsyncClient`` configured to talk to the test app."""
    async with AsyncClient(
        base_url="https://example.com/", transport=ASGITransport(app=app)
    ) as client:
        yield client


@pytest.fixture
def discovery_client(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> DiscoveryClient:
    config_dependency.set_config_path(data_path("config/phalanx.yaml"))
    repertoire_url = TEST_BASE_URL.rstrip("/") + "/repertoire"
    monkeypatch.setenv("REPERTOIRE_BASE_URL", repertoire_url)
    return DiscoveryClient(client)
