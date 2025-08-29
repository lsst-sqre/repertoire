"""Handlers for the app's external root, ``/repertoire/``."""

from typing import Annotated

from fastapi import APIRouter, Depends
from safir.metadata import get_metadata
from safir.slack.webhook import SlackRouteErrorHandler

from rubin.repertoire import Discovery

from ..config import Config
from ..dependencies.config import config_dependency
from ..dependencies.discovery import discovery_dependency
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
    config: Annotated[Config, Depends(config_dependency)],
) -> Index:
    metadata = get_metadata(
        package_name="repertoire", application_name=config.name
    )
    return Index(metadata=metadata)


@external_router.get(
    "/discovery",
    response_model_exclude_none=True,
    summary="Discovery information",
)
async def get_discovery(
    discovery: Annotated[Discovery, Depends(discovery_dependency)],
) -> Discovery:
    return discovery
