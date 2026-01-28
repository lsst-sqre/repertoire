"""Custom exceptions for the Repertoire server."""

from fastapi import status
from safir.fastapi import ClientRequestError
from safir.slack.blockkit import SlackWebException

__all__ = [
    "DatabaseNotFoundError",
    "HipsDatasetNotFoundError",
    "TAPSchemaDirectoryError",
    "TAPSchemaDownloadError",
    "TAPSchemaExtractionError",
    "TAPSchemaMigrationError",
    "TAPSchemaNotFoundError",
    "TAPSchemaStorageError",
    "TAPSchemaValidationError",
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


class TAPSchemaStorageError(SlackWebException):
    """Base exception for schema storage operations."""


class TAPSchemaDownloadError(TAPSchemaStorageError):
    """Raised when schema download fails."""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        schema_version: str | None = None,
    ) -> None:
        super().__init__(message)
        self.url = url
        self.schema_version = schema_version


class TAPSchemaExtractionError(TAPSchemaStorageError):
    """Raised when schema archive extraction fails."""

    def __init__(
        self,
        message: str,
        archive_path: str | None = None,
    ) -> None:
        super().__init__(message)
        self.archive_path = archive_path


class TAPSchemaNotFoundError(TAPSchemaStorageError):
    """Raised when schema file is not found."""

    def __init__(
        self,
        schema_name: str,
        available_schemas: list[str] | None = None,
    ) -> None:
        message = f"Schema not found: {schema_name}.yaml"
        if available_schemas:
            message += f"\nAvailable: {', '.join(available_schemas)}"
        super().__init__(message)
        self.schema_name = schema_name
        self.available_schemas = available_schemas or []


class TAPSchemaMigrationError(SlackWebException):
    """Raised when schema migration/deployment fails."""

    def __init__(
        self,
        message: str,
        schema_version: str | None = None,
        stage: str | None = None,
    ) -> None:
        super().__init__(message)
        self.schema_version = schema_version
        self.stage = stage


class TAPSchemaValidationError(TAPSchemaMigrationError):
    """Raised when schema validation fails."""

    def __init__(
        self,
        message: str,
        schema_version: str | None = None,
        missing_schemas: list[str] | None = None,
    ) -> None:
        super().__init__(message, schema_version, "validation")
        self.missing_schemas = missing_schemas or []


class TAPSchemaDirectoryError(TAPSchemaStorageError):
    """Raised when schema directory structure is invalid."""

    def __init__(
        self,
        message: str,
        schema_dir: str | None = None,
    ) -> None:
        super().__init__(message)
        self.schema_dir = schema_dir
