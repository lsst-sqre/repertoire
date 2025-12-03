"""Declarative base for Repertoire database schema."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase

__all__ = ["SchemaBase"]


class SchemaBase(DeclarativeBase):
    """SQLAlchemy declarative base for Repertoire database schema."""
