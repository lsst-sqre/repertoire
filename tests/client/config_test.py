"""Tests for configuration parsing."""

import yaml
from safir.testing.data import Data

from rubin.repertoire import RepertoireSettings


def test_extra_ignore(data: Data) -> None:
    """Test that extra values intended for the server are ignored."""
    with data.path("config/sentry.yaml").open("r") as fh:
        settings = yaml.safe_load(fh)
    RepertoireSettings.model_validate(settings)
