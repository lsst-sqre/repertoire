"""The main application factory for the Repertoire service."""

import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from importlib.metadata import metadata, version
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from safir.fastapi import ClientRequestError, client_request_error_handler
from safir.middleware.x_forwarded import XForwardedMiddleware
from safir.slack.webhook import SlackRouteErrorHandler

from .constants import SECRETS_PATH
from .dependencies.builder import builder_dependency
from .dependencies.config import config_dependency
from .handlers.external import external_router
from .handlers.internal import internal_router

__all__ = ["create_app"]


def create_app(
    *, load_config: bool = True, secrets_root: str | Path = SECRETS_PATH
) -> FastAPI:
    """Create the FastAPI application.

    This is in a function rather than using a global variable (as is more
    typical for FastAPI) because the configuration is loaded from a YAML file
    and we want to provide a chance for the test suite to configure the
    location of that YAML file.

    Parameters
    ----------
    load_config
        If set to `False`, do not try to load the configuration. This is used
        primarily for OpenAPI schema generation, where constructing the app is
        required but the configuration won't matter.
    secrets_root
        Overrides the default secrets root of :file:`/etc/repertoire/secrets`
        used by the Helm chart and Docker container.
    """
    path_prefix = "/repertoire"
    if load_config:
        config = config_dependency.config()
        path_prefix = config.path_prefix

        # Configure Slack alerts.
        if config.slack_alerts and config.slack_webhook:
            logger = structlog.get_logger("repertoire")
            SlackRouteErrorHandler.initialize(
                config.slack_webhook, "Repertoire", logger
            )
            logger.debug("Initialized Slack webhook")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        builder_dependency.initialize(secrets_root)
        yield

    # Create the application.
    app = FastAPI(
        title="Repertoire",
        description=metadata("repertoire")["Summary"],
        version=version("repertoire"),
        openapi_url=f"{path_prefix}/openapi.json",
        docs_url=f"{path_prefix}/docs",
        redoc_url=f"{path_prefix}/redoc",
        lifespan=lifespan,
    )

    # Attach the routers.
    app.include_router(internal_router)
    app.include_router(external_router, prefix=path_prefix)

    # Add middleware.
    app.add_middleware(XForwardedMiddleware)

    # Add error handlers.
    app.exception_handler(ClientRequestError)(client_request_error_handler)

    # Return the constructed app.
    return app


def create_openapi(*, add_back_link: bool = False) -> str:
    """Generate the OpenAPI schema.

    Parameters
    ----------
    add_back_link
        Whether to add a back link to the parent page to the description.
        This is useful when the schema will be rendered as part of the
        documentation.

    Returns
    -------
    str
        OpenAPI schema as serialized JSON.
    """
    app = create_app(load_config=False)
    description = app.description
    if add_back_link:
        description += "\n\n[Return to Repertoire documentation](index.html)."
    schema = get_openapi(
        title=app.title,
        description=description,
        version=app.version,
        routes=app.routes,
    )
    return json.dumps(schema)
