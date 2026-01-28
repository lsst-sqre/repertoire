"""Tests for the repertoire.handlers.internal module and routes."""

import pytest
from httpx import AsyncClient

from repertoire.dependencies.config import config_dependency


@pytest.mark.asyncio
async def test_get_index(client: AsyncClient) -> None:
    """Test ``GET /``."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == config_dependency.config().name
    assert isinstance(data["version"], str)
    assert isinstance(data["description"], str)
    assert isinstance(data["repository_url"], str)
    assert isinstance(data["documentation_url"], str)
