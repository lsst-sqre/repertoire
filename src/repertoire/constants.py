"""Constants for Repertoire."""

from pathlib import Path

__all__ = ["CONFIG_PATH", "SECRETS_PATH"]

CONFIG_PATH = "/etc/repertoire/config.yaml"
"""Default configuration path."""

SECRETS_PATH = Path("/etc/repertoire/secrets")
"""Default path to secrets, containing one file per secrets key."""
