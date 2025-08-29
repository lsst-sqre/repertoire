"""Test fixtures for Repertoire tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from repertoire.dependencies.config import config_dependency
from repertoire.main import create_app

from .support.data import data_path


@pytest_asyncio.fixture
async def app() -> AsyncGenerator[FastAPI]:
    """Return a configured test application.

    Wraps the application in a lifespan manager so that startup and shutdown
    events are sent during test execution.
    """
    config_dependency.set_config_path(data_path("config/minimal.yaml"))
    app = create_app()
    async with LifespanManager(app):
        yield app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    """Return an ``httpx.AsyncClient`` configured to talk to the test app."""
    async with AsyncClient(
        base_url="https://example.com/", transport=ASGITransport(app=app)
    ) as client:
        yield client
