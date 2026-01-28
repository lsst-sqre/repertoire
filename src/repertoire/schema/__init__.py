"""Schemas for the TAP_SCHEMA database."""

from .base import SchemaBase
from .version import TAPSchemaVersion

__all__ = [
    "SchemaBase",
    "TAPSchemaVersion",
]
