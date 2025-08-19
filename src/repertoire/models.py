"""Models for Repertoire."""

from pydantic import BaseModel, Field
from safir.metadata import Metadata as SafirMetadata

__all__ = ["Index"]


class Index(BaseModel):
    """Metadata returned by the external root URL of the application."""

    metadata: SafirMetadata = Field(..., title="Package metadata")
