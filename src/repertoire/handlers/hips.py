"""Handlers for the HiPS list."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from safir.slack.webhook import SlackRouteErrorHandler

from ..dependencies.hips import hips_list_dependency

__all__ = ["hips_legacy_router", "hips_router"]

hips_router = APIRouter(route_class=SlackRouteErrorHandler)
"""FastAPI router for HiPS list handlers."""

hips_legacy_router = APIRouter(route_class=SlackRouteErrorHandler)
"""FastAPI router for legacy HiPS list handlers."""


@hips_router.get(
    "/{dataset}/list",
    response_class=PlainTextResponse,
    include_in_schema=False,
)
async def get_hips_list(
    *, hips_list: Annotated[str, Depends(hips_list_dependency)]
) -> str:
    return hips_list


@hips_legacy_router.get(
    "/list",
    response_class=PlainTextResponse,
    include_in_schema=False,
)
async def get_legacy_hips_list(
    *,
    hips_list: Annotated[str, Depends(hips_list_dependency.legacy)],
) -> str:
    return hips_list
