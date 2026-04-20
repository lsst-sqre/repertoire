"""VOResource capability models."""

from pydantic import AnyUrl
from pydantic_xml import attr
from vo_models.voresource.models import Capability

from repertoire.registry.constants import (
    SIA_STANDARD_ID,
    SODA_ASYNC_STANDARD_ID,
    SODA_SYNC_STANDARD_ID,
    anyurl,
)


class SimpleImageAccess(Capability, tag="capability"):
    """Capability for an SIA v2 query endpoint."""

    standard_id: AnyUrl | None = attr(
        name="standardID",
        default=anyurl.validate_python(SIA_STANDARD_ID),
    )
    type: str | None = attr(name="type", default=None, ns="xsi", exclude=True)


class SODASync(Capability, tag="capability"):
    """Capability for a SODA synchronous endpoint."""

    standard_id: AnyUrl | None = attr(
        name="standardID",
        default=anyurl.validate_python(SODA_SYNC_STANDARD_ID),
    )
    type: str | None = attr(name="type", default=None, ns="xsi", exclude=True)


class SODAAsync(Capability, tag="capability"):
    """Capability for a SODA asynchronous endpoint."""

    standard_id: AnyUrl | None = attr(
        name="standardID",
        default=anyurl.validate_python(SODA_ASYNC_STANDARD_ID),
    )
    type: str | None = attr(name="type", default=None, ns="xsi", exclude=True)
