"""Handlers for the app's external root, ``/repertoire/``."""

from typing import Annotated

from fastapi import APIRouter, Depends
from safir.dependencies.logger import logger_dependency
from safir.metadata import get_metadata
from safir.slack.webhook import SlackRouteErrorHandler
from structlog.stdlib import BoundLogger

from ..config import config
from ..models import Index

__all__ = ["external_router"]

external_router = APIRouter(route_class=SlackRouteErrorHandler)
"""FastAPI router for all external handlers."""


@external_router.get(
    "/",
    response_model_exclude_none=True,
    summary="Application metadata",
)
async def get_index(
    logger: Annotated[BoundLogger, Depends(logger_dependency)],
) -> Index:
    metadata = get_metadata(
        package_name="repertoire", application_name=config.name
    )
    return Index(metadata=metadata)
