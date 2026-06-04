"""Tests for the service discovery client models."""

import pytest
from safir.testing.data import Data

from rubin.repertoire import Discovery


@pytest.mark.asyncio
async def test_unknown_fields(data: Data) -> None:
    """Ensure unknown fields in the JSON are ignored."""
    output = data.read_json("output/unknown")
    Discovery.model_validate(output)
