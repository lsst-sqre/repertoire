"""Tests for configuration parsing."""

import pytest
import yaml
from pydantic import ValidationError
from safir.testing.data import Data

from rubin.repertoire import InfluxDatabaseConfig, RepertoireSettings


def test_extra_ignore(data: Data) -> None:
    """Test that extra values intended for the server are ignored."""
    with data.path("config/sentry.yaml").open("r") as fh:
        settings = yaml.safe_load(fh)
    RepertoireSettings.model_validate(settings)


def test_influxdb_description_required() -> None:
    """Test that every InfluxDB database requires a description."""
    config = {
        "url": "https://data.example.com/influxdb/",
        "database": "efd",
        "username": "efdreader",
        "passwordKey": "idfdev_efd-password",
        "schemaRegistry": "https://data.example.com/schema-registry/",
    }
    with pytest.raises(ValidationError, match="description"):
        InfluxDatabaseConfig.model_validate(config)
