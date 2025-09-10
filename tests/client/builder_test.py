"""Tests for the discovery data builder."""

from __future__ import annotations

from rubin.repertoire import (
    RepertoireBuilder,
    RepertoireBuilderWithSecrets,
    RepertoireSettings,
)

from ..support.constants import TEST_BASE_URL
from ..support.data import data_path, read_test_json


def test_build_discovery() -> None:
    config_path = data_path("config/phalanx.yaml")
    base_url = TEST_BASE_URL.rstrip("/") + "/repertoire"
    config = RepertoireSettings.from_file(config_path)
    output = RepertoireBuilder(config).build_discovery(base_url)
    output_json = output.model_dump(mode="json", exclude_none=True)
    assert output_json == read_test_json("output/phalanx")


def test_build_influxdb() -> None:
    config_path = data_path("config/phalanx.yaml")
    config = RepertoireSettings.from_file(config_path)
    expected = read_test_json("output/idfdev_efd")

    # This is the version without credentials, so username and password should
    # not be included.
    del expected["username"]
    del expected["password"]

    # Check the output.
    output = RepertoireBuilder(config).build_influxdb("idfdev_efd")
    assert output
    assert output.model_dump(mode="json", exclude_none=True) == expected


def test_build_influxdb_creds() -> None:
    config_path = data_path("config/phalanx.yaml")
    secrets_path = data_path("secrets")
    config = RepertoireSettings.from_file(config_path)

    # First test with a Path parameter to RepertoireBuilderWithSecrets and a
    # secret file ending in a newline.
    builder = RepertoireBuilderWithSecrets(config, secrets_path)
    output = builder.build_influxdb_with_credentials("idfdev_efd")
    assert output
    output_json = output.model_dump(mode="json", exclude_none=True)
    assert output_json == read_test_json("output/idfdev_efd")

    # Now test with a str parameter and a secret file not ending in a newline.
    builder = RepertoireBuilderWithSecrets(config, str(secrets_path))
    output = builder.build_influxdb_with_credentials("idfdev_metrics")
    assert output
    output_json = output.model_dump(mode="json", exclude_none=True)
    assert output_json == read_test_json("output/idfdev_metrics")

    # Unknown InfluxDB databases should return None.
    assert builder.build_influxdb("invalid") is None
