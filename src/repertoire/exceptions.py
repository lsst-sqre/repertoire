"""Custom exceptions for the Repertoire server."""

from __future__ import annotations

from fastapi import status
from safir.fastapi import ClientRequestError

__all__ = ["DatabaseNotFoundError"]


class DatabaseNotFoundError(ClientRequestError):
    """Requested InfluxDB database not found."""

    error = "database_not_found"
    status_code = status.HTTP_404_NOT_FOUND
