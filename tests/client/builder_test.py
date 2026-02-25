"""Tests for the discovery data builder."""

from safir.testing.data import Data

from rubin.repertoire import (
    RepertoireBuilder,
    RepertoireBuilderWithSecrets,
    RepertoireSettings,
)

from ..support.constants import TEST_BASE_URL


def test_build_discovery(data: Data) -> None:
    config_path = data.path("config/phalanx.yaml")
    hips_base_url = TEST_BASE_URL.rstrip("/")
    base_url = hips_base_url + "/repertoire"
    config = RepertoireSettings.from_file(config_path)

    output = RepertoireBuilder(config).build_discovery(base_url, hips_base_url)
    output_json = output.model_dump(mode="json", exclude_defaults=True)
    data.assert_json_matches(output_json, "output/phalanx")

    output = RepertoireBuilder(config).build_discovery(base_url)
    for dataset in output.datasets:
        assert "hips" not in output.datasets[dataset].services


def test_build_influxdb(data: Data) -> None:
    config_path = data.path("config/phalanx.yaml")
    config = RepertoireSettings.from_file(config_path)

    # Check the output.
    output = RepertoireBuilder(config).build_influxdb("idfdev_efd")
    assert output
    data.assert_pydantic_matches(
        output, "output/idfdev_efd", exclude_defaults=True
    )


def test_build_influxdb_creds(data: Data) -> None:
    config_path = data.path("config/phalanx.yaml")
    secrets_path = data.path("secrets")
    config = RepertoireSettings.from_file(config_path)

    # First test with a Path parameter to RepertoireBuilderWithSecrets and a
    # secret file ending in a newline.
    builder = RepertoireBuilderWithSecrets(config, secrets_path)
    output = builder.build_influxdb_with_credentials("idfdev_efd")
    assert output
    data.assert_pydantic_matches(
        output, "output/idfdev_efd-creds", exclude_defaults=True
    )

    # Now test with a str parameter and a secret file not ending in a newline.
    builder = RepertoireBuilderWithSecrets(config, str(secrets_path))
    output = builder.build_influxdb_with_credentials("idfdev_metrics")
    assert output
    data.assert_pydantic_matches(
        output, "output/idfdev_metrics-creds", exclude_defaults=True
    )

    # Unknown InfluxDB databases should return None.
    assert builder.build_influxdb("invalid") is None


def test_list_influxdb_creds(data: Data) -> None:
    config_path = data.path("config/phalanx.yaml")
    secrets_path = data.path("secrets")
    config = RepertoireSettings.from_file(config_path)

    builder = RepertoireBuilderWithSecrets(config, secrets_path)
    output = builder.list_influxdb_with_credentials()
    assert list(output.keys()) == ["idfdev_efd", "idfdev_metrics"]
    data.assert_pydantic_matches(
        output["idfdev_efd"], "output/idfdev_efd-creds", exclude_defaults=True
    )
    data.assert_pydantic_matches(
        output["idfdev_metrics"],
        "output/idfdev_metrics-creds",
        exclude_defaults=True,
    )
