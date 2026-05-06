"""VOResource capability and service models."""

from pydantic import AnyUrl
from pydantic_xml import attr, element
from vo_models.tapregext.models import TableAccess
from vo_models.voresource.models import Capability, Service

from rubin.repertoire import IvoaStandardId


class SimpleImageAccess(Capability, tag="capability"):
    """Capability for an SIA v2 query endpoint."""

    standard_id: AnyUrl | None = attr(
        name="standardID",
        default=IvoaStandardId.SIA_QUERY_2,
    )
    type: str | None = attr(name="type", default=None, ns="xsi", exclude=True)


class SODASync(Capability, tag="capability"):
    """Capability for a SODA synchronous endpoint."""

    standard_id: AnyUrl | None = attr(
        name="standardID",
        default=IvoaStandardId.SODA_SYNC_1,
    )
    type: str | None = attr(name="type", default=None, ns="xsi", exclude=True)


class SODAAsync(Capability, tag="capability"):
    """Capability for a SODA asynchronous endpoint."""

    standard_id: AnyUrl | None = attr(
        name="standardID",
        default=IvoaStandardId.SODA_ASYNC_1,
    )
    type: str | None = attr(name="type", default=None, ns="xsi", exclude=True)


class TypedService(Service, tag="Service"):
    """Service with a typed capability list to preserve subclass fields.

    Using a union here causes pydantic-xml to dispatch on the runtime
    type, preserving the subclass elements, otherwise if we just use
    ``Service`` pydantic-xml serializes using the base-class schema
    and drops the subclass fields.
    """

    capability: (
        list[
            TableAccess | SODASync | SODAAsync | SimpleImageAccess | Capability
        ]
        | None
    ) = element(tag="capability", default_factory=list)
