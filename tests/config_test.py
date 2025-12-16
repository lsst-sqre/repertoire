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


def test_tap_server_config_defaults() -> None:
    config = Config.from_file(data_path("config/tap.yaml"))
    tap_server = config.tap.servers["tap"]
    assert tap_server.database_host == "127.0.0.1"
    assert tap_server.database_port == 5432


def test_tap_server_config_custom_host_port() -> None:
    config = Config.from_file(data_path("config/tap-custom.yaml"))
    tap_server = config.tap.servers["tap"]
    assert tap_server.database_host == "example.database.host"
    assert tap_server.database_port == 5433
