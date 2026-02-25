"""Test fixtures for Repertoire tests."""

from collections.abc import AsyncGenerator, AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
import respx
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from jinja2 import Template
from pydantic import SecretStr
from safir.logging import LogLevel, Profile, configure_logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from structlog.stdlib import BoundLogger, get_logger
from testcontainers.postgres import PostgresContainer

from repertoire.config import Config
from repertoire.dependencies.config import config_dependency
from repertoire.dependencies.hips import hips_list_dependency
from repertoire.main import create_app
from rubin.repertoire import DiscoveryClient

from .support.constants import TEST_BASE_URL
from .support.data import data_path
from .support.hips import register_mock_hips


@pytest_asyncio.fixture(params=["phalanx"])
async def app(
    request: pytest.FixtureRequest, token: str
) -> AsyncGenerator[FastAPI]:
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
    config = config_dependency.config()
    if config.hips and config.hips.datasets:
        config.token = SecretStr(token)
    hips_list_dependency.clear_cache()
    app = create_app(secrets_root=data_path("secrets"))
    async with LifespanManager(app):
        yield app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    """Return an ``httpx.AsyncClient`` configured to talk to the test app."""
    async with AsyncClient(
        base_url="https://example.com/",
        headers={"X-Auth-Request-User": "username"},
        transport=ASGITransport(app=app),
    ) as client:
        yield client


@pytest.fixture
def discovery(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> DiscoveryClient:
    repertoire_url = TEST_BASE_URL.rstrip("/") + "/repertoire"
    return DiscoveryClient(client, base_url=repertoire_url)


@pytest.fixture(autouse=True)
def mock_hips(
    respx_mock: respx.Router, monkeypatch: pytest.MonkeyPatch, token: str
) -> None:
    monkeypatch.setenv("REPERTOIRE_TOKEN", token)
    config = Config.from_file(data_path("config/phalanx.yaml"))
    assert config.hips
    monkeypatch.delenv("REPERTOIRE_TOKEN")
    template = Template(config.hips.source_template)
    for dataset in config.hips.datasets:
        context = {"base_hostname": config.base_hostname, "dataset": dataset}
        register_mock_hips(respx_mock, template.render(**context))


@pytest.fixture(scope="session")
def token() -> str:
    token_path = Path(__file__).parent / "data" / "secrets" / "token"
    return token_path.read_text().rstrip("\n")


@pytest.fixture(scope="session")
def postgres_container() -> Iterator[PostgresContainer]:
    """Start a PostgreSQL container for the test session."""
    container = PostgresContainer("postgres:15-alpine")
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def database_url(postgres_container: PostgresContainer) -> str:
    """Get the database URL from the container."""
    url = postgres_container.get_connection_url()
    return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")


@pytest.fixture(scope="session")
def database_password(postgres_container: PostgresContainer) -> str:
    """Get the database password from the container."""
    return postgres_container.password


@pytest_asyncio.fixture(scope="function")
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    """Create a database engine connected to the test container."""
    _engine = create_async_engine(database_url, echo=False)

    async with _engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS tap_schema CASCADE"))
        await conn.execute(
            text("DROP SCHEMA IF EXISTS tap_schema_staging CASCADE")
        )

    yield _engine

    async with _engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS tap_schema CASCADE"))
        await conn.execute(
            text("DROP SCHEMA IF EXISTS tap_schema_staging CASCADE")
        )

    await _engine.dispose()


@pytest.fixture
def logger() -> BoundLogger:
    """Create a test debug logger."""
    configure_logging(
        profile=Profile.production, log_level=LogLevel.DEBUG, name="test"
    )
    return get_logger("test")


@pytest.fixture
def tap_config_file(tmp_path: Path) -> Path:
    """Create a config file for TAP schema CLI tests.

    Note: Database credentials are overridden via --database-url in tests.
    """
    return data_path("config/tap.yaml")
