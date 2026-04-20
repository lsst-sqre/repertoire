"""Handlers for the IVOA OAI-PMH publishing registry endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from safir.slack.webhook import SlackRouteErrorHandler
from starlette.datastructures import UploadFile

from ..dependencies.registry import oai_handler_dependency
from ..registry.oai import OaiHandler, OaiParameters

__all__ = ["registry_router"]

registry_router = APIRouter(route_class=SlackRouteErrorHandler)
"""FastAPI router for the IVOA publishing registry."""


async def oai_params(request: Request) -> OaiParameters:
    """Extract OAI-PMH parameters from a GET query string or POST form body.

    OAI-PMH 2.0 requires repositories to support both GET and POST.
    Populates ``has_duplicate_params`` when any parameter key appears more
    than once, and ``provided_args`` with the set of keys actually present
    (used by ``OaiHandler`` to detect forbidden arguments per verb).

    Parameters
    ----------
    request
        The incoming HTTP request.

    Returns
    -------
    OaiParameters
        Parsed OAI-PMH parameters.
    """
    if request.method == "POST":
        form = await request.form()
        items = [
            (k, v)
            for k, v in form.multi_items()
            if not isinstance(v, UploadFile)
        ]
    else:
        items = list(request.query_params.multi_items())

    seen: set[str] = set()
    has_duplicates = False
    for key, _ in items:
        if key in seen:
            has_duplicates = True
        seen.add(key)

    return OaiParameters.model_validate(
        {
            **dict(items),
            "has_duplicate_params": has_duplicates,
            "provided_args": frozenset(seen),
        }
    )


@registry_router.api_route(
    "/oai",
    methods=["GET", "POST"],
    summary="IVOA Publishing Registry",
)
async def get_oai(
    params: Annotated[OaiParameters, Depends(oai_params)],
    handler: Annotated[OaiHandler, Depends(oai_handler_dependency)],
) -> Response:
    """Handle an OAI-PMH request.

    Accepts any OAI-PMH verb as a query parameter (GET) or form field
    (POST) and returns the corresponding XML response.  All responses
    (including errors) use HTTP 200 as specified in OAI-PMH.
    """
    return Response(content=handler.handle(params), media_type="text/xml")
