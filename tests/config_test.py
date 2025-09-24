"""Tests for configuration parsing."""

from __future__ import annotations

from repertoire.config import Config

from .support.data import data_path


def test_config_sentry() -> None:
    config = Config.from_file(data_path("config/phalanx.yaml"))
    assert not config.sentry
    config = Config.from_file(data_path("config/sentry.yaml"))
    assert config.sentry
    assert config.sentry.enabled
