"""Custom exceptions for the Repertoire server."""

from __future__ import annotations

from fastapi import status
from safir.fastapi import ClientRequestError
from safir.slack.blockkit import SlackWebException

__all__ = [
    "DatabaseNotFoundError",
    "HipsDatasetNotFoundError",
]


class DatabaseNotFoundError(ClientRequestError):
    """Requested InfluxDB database not found."""

    error = "database_not_found"
    status_code = status.HTTP_404_NOT_FOUND


class HipsDatasetNotFoundError(ClientRequestError):
    """Requested HiPS dataset not found."""

    error = "hips_not_found"
    status_code = status.HTTP_404_NOT_FOUND


class HipsWebError(SlackWebException):
    """Error retrieving properties file for HiPS list."""
