"""Metrics events for Repertoire."""

from typing import override

from pydantic import Field
from safir.dependencies.metrics import EventDependency, EventMaker
from safir.metrics import EventManager, EventPayload

__all__ = [
    "Events",
    "InfluxCredentialsEvent",
    "events_dependency",
]


class InfluxCredentialsEvent(EventPayload):
    """Processed request for InfluxDB credentials."""

    username: str = Field(
        ..., title="Username", description="Username of authenticated user"
    )

    label: str = Field(
        ...,
        title="InfluxDB label",
        description=(
            "InfluxDB database label for which credentials were requested"
        ),
    )


class Events(EventMaker):
    """Event publishers for all possible events.

    Attributes
    ----------
    influx_creds
        User retrieved InfluxDB credentials.
    """

    @override
    async def initialize(self, manager: EventManager) -> None:
        self.influx_creds = await manager.create_publisher(
            "influxdb_credentials", InfluxCredentialsEvent
        )


events_dependency = EventDependency(Events())
"""FastAPI dependency for the event publishers."""
