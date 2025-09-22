"""Test fixtures for Repertoire tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
import respx
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from jinja2 import Template

from repertoire.config import Config
from repertoire.dependencies.config import config_dependency
from repertoire.main import create_app
from rubin.repertoire import DiscoveryClient

from .support.constants import TEST_BASE_URL
from .support.data import data_path
from .support.hips import register_mock_hips


@pytest_asyncio.fixture(params=["phalanx"])
async def app(request: pytest.FixtureRequest) -> AsyncGenerator[FastAPI]:
    """Return a configured test application.

    Wraps the application in a lifespan manager so that startup and shutdown
    events are sent during test execution.

    Examples
    --------
    Add the following mark before tests that should use a different
    configuration file for the application.

    .. code-block:: python

       @pytest.mark.asyncio
       @pytest.mark.parameterize("app", ["minimal"], indirect=True)
       async def test_something() -> None: ...
    """
    config_path = f"config/{request.param}.yaml"
    config_dependency.set_config_path(data_path(config_path))
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


@pytest.fixture(autouse=True)
def mock_hips(respx_mock: respx.Router) -> None:
    config = Config.from_file(data_path("config/phalanx.yaml"))
    assert config.hips
    template = Template(config.hips.source_template)
    for dataset in config.hips.datasets:
        context = {"base_hostname": config.base_hostname, "dataset": dataset}
        register_mock_hips(respx_mock, template.render(**context))
