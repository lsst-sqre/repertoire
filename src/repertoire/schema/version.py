"""SQLAlchemy schema for TAP_SCHEMA version table."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import TIMESTAMP, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import SchemaBase

__all__ = ["TAPSchemaVersion"]


class TAPSchemaVersion(SchemaBase):
    """Table holding TAP_SCHEMA version information."""

    __tablename__ = "version11"
    __table_args__ = ({"schema": "tap_schema_staging"},)

    version: Mapped[str] = mapped_column(String, primary_key=True)
    loaded_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
    )
