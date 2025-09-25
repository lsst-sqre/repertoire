"""Models for Repertoire service discovery."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl, PlainSerializer, SecretStr

__all__ = [
    "ApiService",
    "ApiVersion",
    "BaseService",
    "DataService",
    "Dataset",
    "Discovery",
    "InfluxDatabase",
    "InfluxDatabaseWithCredentials",
    "InternalService",
    "Services",
    "UiService",
]


class Dataset(BaseModel):
    """Discovery information about a single dataset."""

    butler_config: Annotated[
        HttpUrl | None,
        Field(
            title="Butler config URL",
            description=(
                "URL of Butler configuration to access this dataset, if it is"
                " available via a Butler server"
            ),
            examples=["https://example.org/api/butler/repo/dp02/butler.yaml"],
        ),
    ] = None

    description: Annotated[
        str,
        Field(
            title="Description",
            description="Long description of the dataset",
            examples=[
                "Data Preview 1 contains the first image data from the"
                " telescope during commissioning"
            ],
        ),
    ]

    hips_list: Annotated[
        HttpUrl | None,
        Field(
            title="HiPS list URL",
            description=(
                "URL to the HiPS list collecting HiPS surveys for this dataset"
            ),
            examples=["https://example.org/api/hips/dp02/list"],
        ),
    ] = None


class InfluxDatabase(BaseModel):
    """Connection information for an InfluxDB database."""

    url: Annotated[
        HttpUrl,
        Field(
            title="InfluxDB URL",
            description="URL to InfluxDB service",
            examples=["https://example.org/influxdb/"],
        ),
    ]

    database: Annotated[
        str,
        Field(
            title="Name of InfluxDB database",
            description="Name of database to include in queries",
            examples=["efd", "lsst.square.metrics"],
        ),
    ]

    schema_registry: Annotated[
        HttpUrl,
        Field(
            title="Schema registry URL",
            description="URL of corresponding Confluent schema registry",
            examples=["https://example.org/schema-registry"],
        ),
    ]


class InfluxDatabaseWithCredentials(InfluxDatabase):
    """InfluxDB database connection information with credentials."""

    username: Annotated[
        str | None,
        Field(
            title="Client username",
            description="Username to send for authentication",
            examples=["efdreader"],
        ),
    ]

    password: Annotated[
        SecretStr | None,
        Field(
            title="Client password",
            description="Password to send for authentication",
            examples=["password"],
        ),
        PlainSerializer(lambda p: p.get_secret_value(), when_used="json"),
    ]


class InfluxDatabaseWithPointer(InfluxDatabase):
    """InfluxDB database connection information with credential pointer.

    This is returned by the unauthenticated discovery route and contains a
    pointer to the authenticated endpoint to get credential information.
    """

    credentials_url: Annotated[
        HttpUrl,
        Field(
            title="URL for credentials",
            description=(
                "Authenticated endpoint that will return full connection"
                " information including authentication credentials"
            ),
            examples=["https://example.com/discovery/influxdb/efd"],
        ),
    ]


class ApiVersion(BaseModel):
    """One version of a REST API."""

    url: Annotated[
        HttpUrl,
        Field(
            title="Service URL",
            description="Access URL for that version of the service",
            examples=["https://example.org/api/cutout/sync"],
        ),
    ]

    ivoa_standard_id: Annotated[
        str | None,
        Field(
            title="IVOA standardID",
            description="IVOA standardID used in service registrations",
            examples=["ivo://ivoa.net/std/SODA#async-1.0"],
        ),
    ] = None


class BaseService(BaseModel):
    """Base model for services."""

    url: Annotated[
        HttpUrl,
        Field(
            title="Service URL",
            description="Default access URL for the service",
            examples=["https://example.org/api/cutout"],
        ),
    ]


class ApiService(BaseService):
    """Base model for services with an API."""

    openapi: Annotated[
        HttpUrl | None,
        Field(
            title="OpenAPI schema",
            description=(
                "URL to the OpenAPI schema for the service if available"
            ),
            examples=["https://example.org/api/cutout/openapi.json"],
        ),
    ] = None

    versions: Annotated[
        dict[str, ApiVersion],
        Field(
            title="API versions",
            description=(
                "Discovery information for each API version, if the service"
                " may have multiple versions"
            ),
        ),
    ] = {}


class DataService(ApiService):
    """A user-facing API service tied to a particular dataset."""


class InternalService(ApiService):
    """An internal API service not tied to a particular dataset."""


class UiService(BaseService):
    """A user interface service."""


class Services(BaseModel):
    """Mappings of service names to service information."""

    data: Annotated[
        dict[str, dict[str, DataService]],
        Field(
            title="Data services",
            description=(
                "Mapping of service names to dataset names served by that"
                " service to service information. The dataset name will match"
                " the name of one of the datasets in the associated discovery"
                " reply. These are the API services used directly by users"
                " for data access."
            ),
            examples=[
                {
                    "cutout": {
                        "dp02": {
                            "url": "https://example.org/api/cutout/dp02",
                            "openapi": "https://example.org/api/cutout/openapi",
                        },
                        "dp1": {
                            "url": "https://example.org/api/cutout/dp1",
                            "openapi": "https://example.org/api/cutout/openapi",
                        },
                    },
                }
            ],
        ),
    ] = {}

    internal: Annotated[
        dict[str, InternalService],
        Field(
            title="Internal service",
            description=(
                "Mapping of service name to service information for internal"
                " services. These are used by other services and generally"
                " won't be used directly by users."
            ),
            examples=[
                {
                    "gafaelfawr": {
                        "url": "https://example.org/auth/api/v1",
                        "openapi": "https://example.org/auth/openapi.json",
                    },
                    "wobbly": {
                        "url": "https://example.org/wobbly",
                        "openapi": "https://example.org/wobbly/openapi.json",
                    },
                }
            ],
        ),
    ] = {}

    ui: Annotated[
        dict[str, UiService],
        Field(
            title="User interfaces",
            description=(
                "Mapping of service name to service information for user"
                " interfaces intended for access by a user using a web"
                " browser."
            ),
            examples=[
                {
                    "argocd": {"url": "https://example.org/argo-cd"},
                    "nublado": {"url": "https://nb.example.org/nb"},
                }
            ],
        ),
    ] = {}


class Discovery(BaseModel):
    """Service discovery information."""

    applications: Annotated[
        list[str],
        Field(
            title="Phalanx applications",
            description=(
                "Names of all Phalanx applications enabled in the local"
                " environment"
            ),
            examples=[
                ["argocd", "gafaelfawr", "hips", "mobu", "nublado", "wobbly"]
            ],
        ),
    ] = []

    datasets: Annotated[
        dict[str, Dataset],
        Field(
            title="Datasets",
            description="All datasets available in the local environment",
        ),
    ] = {}

    influxdb_databases: Annotated[
        dict[str, InfluxDatabaseWithPointer],
        Field(
            title="Available InfluxDB databases",
            description=(
                "Mapping of short names of InfluxDB databases accessible from"
                " this Phalanx environment to connection information"
            ),
        ),
    ] = {}

    services: Annotated[
        Services,
        Field(
            title="Service URLs",
            description="URLs to services available in the local environment",
        ),
    ]
