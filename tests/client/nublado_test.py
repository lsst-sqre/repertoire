"""Tests for generation of stripped-down discovery information for Nublado."""

import pytest
from safir.testing.data import Data

from rubin.repertoire import Discovery, DiscoveryClient


@pytest.mark.asyncio
async def test_nublado(data: Data, discovery: DiscoveryClient) -> None:
    nublado = await discovery.build_nublado_dict()
    data.assert_json_matches(nublado, "output/nublado")


def test_nublado_roundtrip(data: Data) -> None:
    """Test that the reduced output can round-trip through the model."""
    output = data.read_json("output/nublado")
    assert Discovery.model_validate(output).to_nublado_dict() == output
