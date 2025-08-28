"""Tests for the discovery data builder."""

from __future__ import annotations

from rubin.repertoire import RepertoireBuilder, RepertoireConfig

from ..support.data import data_path, read_test_json


def test_builder() -> None:
    config_path = data_path("config/phalanx.yaml")
    config = RepertoireConfig.from_file(config_path)
    output = RepertoireBuilder(config).build()
    output_json = output.model_dump(mode="json", exclude_none=True)
    assert output_json == read_test_json("output/phalanx")
