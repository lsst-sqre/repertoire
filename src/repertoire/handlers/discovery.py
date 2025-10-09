"""Handlers for the Repertoire discovery API."""

from typing import Annotated

from fastapi import APIRouter, Depends
from safir.dependencies.gafaelfawr import (
    auth_dependency,
    auth_logger_dependency,
)
from safir.metadata import get_metadata
from safir.models import ErrorLocation
from safir.slack.webhook import SlackRouteErrorHandler
from structlog.stdlib import BoundLogger

from rubin.repertoire import (
    Discovery,
    InfluxDatabaseWithCredentials,
    RepertoireBuilderWithSecrets,
)

from ..config import Config
from ..dependencies.builder import builder_dependency
from ..dependencies.config import config_dependency
from ..dependencies.discovery import discovery_dependency
from ..dependencies.events import (
    Events,
    InfluxCredentialsEvent,
    events_dependency,
)
from ..exceptions import DatabaseNotFoundError
from ..models import Index

__all__ = ["discovery_router"]

discovery_router = APIRouter(route_class=SlackRouteErrorHandler)
"""FastAPI router for all external handlers."""


@discovery_router.get(
    "/",
    response_model_exclude_none=True,
    summary="Application metadata",
)
async def get_root(
    config: Annotated[Config, Depends(config_dependency)],
) -> Index:
    metadata = get_metadata(
        package_name="repertoire", application_name=config.name
    )
    return Index(metadata=metadata)


@discovery_router.get(
    "/discovery",
    response_model_exclude_none=True,
    summary="Discovery information",
)
async def get_discovery(
    discovery: Annotated[Discovery, Depends(discovery_dependency)],
) -> Discovery:
    return discovery


@discovery_router.get(
    "/discovery/influxdb",
    response_model_exclude_none=True,
    summary="List InfluxDB connection details",
    description=(
        "Returns a dictionary of InfluxDB database labels to connection"
        " information, with credentials, for all databases the user has"
        " access to."
    ),
)
async def list_influxdb(
    builder: Annotated[
        RepertoireBuilderWithSecrets, Depends(builder_dependency)
    ],
    events: Annotated[Events, Depends(events_dependency)],
    logger: Annotated[BoundLogger, Depends(auth_logger_dependency)],
    username: Annotated[str, Depends(auth_dependency)],
) -> dict[str, InfluxDatabaseWithCredentials]:
    result = builder.list_influxdb_with_credentials()
    for database in result:
        event = InfluxCredentialsEvent(username=username, label=database)
        await events.influx_creds.publish(event)
    return result


@discovery_router.get(
    "/discovery/influxdb/{database}",
    response_model_exclude_none=True,
    summary="InfluxDB connection information",
)
async def get_influxdb(
    database: str,
    builder: Annotated[
        RepertoireBuilderWithSecrets, Depends(builder_dependency)
    ],
    events: Annotated[Events, Depends(events_dependency)],
    logger: Annotated[BoundLogger, Depends(auth_logger_dependency)],
    username: Annotated[str, Depends(auth_dependency)],
) -> InfluxDatabaseWithCredentials:
    result = builder.build_influxdb_with_credentials(database)
    if result is None:
        msg = f"Database {database} not found"
        raise DatabaseNotFoundError(msg, ErrorLocation.path, ["database"])
    logger.info("Retrieved InfluxDB credentials", label=database)
    event = InfluxCredentialsEvent(username=username, label=database)
    await events.influx_creds.publish(event)
    return result
