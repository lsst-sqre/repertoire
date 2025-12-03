"""Schemas for the TAP_SCHEMA database."""

from __future__ import annotations

from .base import SchemaBase
from .version import TAPSchemaVersion

__all__ = [
    "SchemaBase",
    "TAPSchemaVersion",
]
