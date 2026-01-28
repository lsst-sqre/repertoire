"""Tests for generation of stripped-down discovery information for Nublado."""

import pytest

from rubin.repertoire import Discovery, DiscoveryClient

from ..support.data import read_test_json


@pytest.mark.asyncio
async def test_nublado(discovery: DiscoveryClient) -> None:
    output = read_test_json("output/nublado")
    assert await discovery.build_nublado_dict() == output


def test_nublado_roundtrip() -> None:
    """Test that the reduced output can round-trip through the model."""
    output = read_test_json("output/nublado")
    assert Discovery.model_validate(output).to_nublado_dict() == output
