"""Tests for generation of stripped-down discovery information for Nublado."""

from __future__ import annotations

import pytest

from rubin.repertoire import DiscoveryClient

from ..support.data import read_test_json


@pytest.mark.asyncio
async def test_nublado(discovery: DiscoveryClient) -> None:
    output = read_test_json("output/nublado")
    assert await discovery.build_nublado_dict() == output
