"""Tests for configuration parsing."""

from safir.testing.data import Data

from repertoire.config import Config


def test_config_sentry(data: Data) -> None:
    config = Config.from_file(data.path("config/phalanx.yaml"))
    assert not config.sentry
    config = Config.from_file(data.path("config/sentry.yaml"))
    assert config.sentry
    assert config.sentry.enabled


def test_tap_server_config_defaults(data: Data) -> None:
    config = Config.from_file(data.path("config/tap.yaml"))
    tap_server = config.tap.servers["tap"]
    assert tap_server.database_url == "postgresql://test@127.0.0.1:5432/test"


def test_tap_server_config_custom_url(data: Data) -> None:
    config = Config.from_file(data.path("config/tap-custom.yaml"))
    tap_server = config.tap.servers["tap"]
    expected = "postgresql://test@example.database.host:5433/test"
    assert tap_server.database_url == expected
