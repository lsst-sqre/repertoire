"""The main application factory for the Repertoire service."""

from importlib.metadata import metadata, version

import structlog
from fastapi import FastAPI
from safir.middleware.x_forwarded import XForwardedMiddleware
from safir.slack.webhook import SlackRouteErrorHandler

from .dependencies.config import config_dependency
from .handlers.external import external_router
from .handlers.internal import internal_router

__all__ = ["create_app"]


def create_app() -> FastAPI:
    """Create the FastAPI application.

    This is in a function rather than using a global variable (as is more
    typical for FastAPI) because the configuration is loaded from a YAML file
    and we want to provide a chance for the test suite to configure the
    location of that YAML file.
    """
    config = config_dependency.config()
    app = FastAPI(
        title="Repertoire",
        description=metadata("repertoire")["Summary"],
        version=version("repertoire"),
        openapi_url=f"{config.path_prefix}/openapi.json",
        docs_url=f"{config.path_prefix}/docs",
        redoc_url=f"{config.path_prefix}/redoc",
    )

    # Attach the routers.
    app.include_router(internal_router)
    app.include_router(external_router, prefix=f"{config.path_prefix}")

    # Add middleware.
    app.add_middleware(XForwardedMiddleware)

    # Configure Slack alerts.
    if config.slack_alerts and config.slack_webhook:
        logger = structlog.get_logger("repertoire")
        SlackRouteErrorHandler.initialize(
            config.slack_webhook, "Repertoire", logger
        )
        logger.debug("Initialized Slack webhook")

    # Return the constructed app.
    return app
