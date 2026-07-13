"""VOResource capability and service models."""

from typing import Literal

from pydantic import AnyUrl
from pydantic_xml import attr, element
from vo_models.tapregext.models import TableAccess
from vo_models.voresource.models import (
    Capability,
    Organisation,
    ResourceName,
    Rights,
    Service,
)

from rubin.repertoire import IvoaStandardId

_RESOURCE_NSMAP = {
    "vr": "http://www.ivoa.net/xml/VOResource/v1.0",
    "vs": "http://www.ivoa.net/xml/VODataService/v1.1",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "ri": "http://www.ivoa.net/xml/RegistryInterface/v1.0",
}


class GroupMembershipService(Capability, tag="capability"):
    """Capability for a GMS v1 query endpoint."""

    standard_id: AnyUrl | None = attr(
        name="standardID",
        default=IvoaStandardId.GMS_SEARCH_1,
    )
    type: str | None = attr(name="type", default=None, ns="xsi", exclude=True)


class SimpleImageAccess(Capability, tag="capability"):
    """Capability for an SIA v2 query endpoint."""

    standard_id: AnyUrl | None = attr(
        name="standardID",
        default=IvoaStandardId.SIA_QUERY_2,
    )
    type: str | None = attr(name="type", default=None, ns="xsi", exclude=True)


class TapAux(Capability, tag="capability"):
    """Capability for a TAP auxiliary endpoint."""

    standard_id: AnyUrl | None = attr(
        name="standardID",
        default=IvoaStandardId.TAP_AUX,
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


class VOSICapabilities(Capability, tag="capability"):
    """Capability for the VOSI capabilities endpoint."""

    standard_id: AnyUrl | None = attr(
        name="standardID",
        default=IvoaStandardId.VOSI_CAPABILITIES,
    )
    type: str | None = attr(name="type", default=None, ns="xsi", exclude=True)


class VOSIAvailability(Capability, tag="capability"):
    """Capability for the VOSI availability endpoint."""

    standard_id: AnyUrl | None = attr(
        name="standardID",
        default=IvoaStandardId.VOSI_AVAILABILITY,
    )
    type: str | None = attr(name="type", default=None, ns="xsi", exclude=True)


class VOSITables(Capability, tag="capability"):
    """Capability for the VOSI tables endpoint."""

    standard_id: AnyUrl | None = attr(
        name="standardID",
        default=IvoaStandardId.VOSI_TABLES,
    )
    type: str | None = attr(name="type", default=None, ns="xsi", exclude=True)


class PlainService(Service, tag="Resource", nsmap=_RESOURCE_NSMAP, ns="ri"):
    """Service serialized as ``<ri:Resource xsi:type="vr:Service">``.

    Using a union in ``capability`` causes pydantic-xml to dispatch on the
    runtime type, preserving subclass elements that would otherwise be dropped
    when serializing through the base ``Capability`` schema.
    """

    type: Literal["vr:Service"] = attr(ns="xsi", default="vr:Service")
    facility: list[ResourceName] = element(
        tag="facility", ns="", default_factory=list
    )
    instrument: list[ResourceName] = element(
        tag="instrument", ns="", default_factory=list
    )
    rights: list[Rights] | None = element(
        tag="rights", ns="", default_factory=list
    )
    capability: list[GroupMembershipService | Capability] | None = element(
        tag="capability", default_factory=list
    )


class TypedService(Service, tag="Resource", nsmap=_RESOURCE_NSMAP, ns="ri"):
    """Service serialized as ``<ri:Resource xsi:type="vs:CatalogService">``.

    Using a union in ``capability`` causes pydantic-xml to dispatch on the
    runtime type, preserving subclass elements that would otherwise be dropped
    when serializing through the base ``Capability`` schema.
    """

    type: Literal["vs:CatalogService"] = attr(
        ns="xsi", default="vs:CatalogService"
    )
    facility: list[ResourceName] = element(
        tag="facility", ns="", default_factory=list
    )
    instrument: list[ResourceName] = element(
        tag="instrument", ns="", default_factory=list
    )
    rights: list[Rights] | None = element(
        tag="rights", ns="", default_factory=list
    )
    capability: (
        list[
            TableAccess
            | SODASync
            | SODAAsync
            | SimpleImageAccess
            | VOSICapabilities
            | VOSIAvailability
            | VOSITables
            | Capability
        ]
        | None
    ) = element(tag="capability", default_factory=list)


class DataResource(Service, tag="Resource", nsmap=_RESOURCE_NSMAP, ns="ri"):
    """Resource serialized as ``<ri:Resource xsi:type="vs:DataResource">``.

    Used for dataset collection records that serve as the resolvable target
    for per-object IVOIDs (Butler datasets, HiPS surveys).
    """

    type: Literal["vs:DataResource"] = attr(
        ns="xsi", default="vs:DataResource"
    )
    facility: list[ResourceName] = element(
        tag="facility", ns="", default_factory=list
    )
    instrument: list[ResourceName] = element(
        tag="instrument", ns="", default_factory=list
    )
    rights: list[Rights] | None = element(
        tag="rights", ns="", default_factory=list
    )


class CatalogResource(Service, tag="Resource", nsmap=_RESOURCE_NSMAP, ns="ri"):
    """Resource serialized as:
    ``<ri:Resource xsi:type="vs:CatalogResource">``.
    """

    type: Literal["vs:CatalogResource"] = attr(
        ns="xsi", default="vs:CatalogResource"
    )
    facility: list[ResourceName] = element(
        tag="facility", ns="", default_factory=list
    )
    instrument: list[ResourceName] = element(
        tag="instrument", ns="", default_factory=list
    )
    rights: list[Rights] | None = element(
        tag="rights", ns="", default_factory=list
    )
    capability: list[TapAux | Capability] | None = element(
        tag="capability", default_factory=list
    )


class TypedDataService(
    Service, tag="Resource", nsmap=_RESOURCE_NSMAP, ns="ri"
):
    """DataService serialized as:
    ``<ri:Resource xsi:type="vs:DataService">``.
    """

    type: Literal["vs:DataService"] = attr(ns="xsi", default="vs:DataService")
    facility: list[ResourceName] = element(
        tag="facility", ns="", default_factory=list
    )
    instrument: list[ResourceName] = element(
        tag="instrument", ns="", default_factory=list
    )
    rights: list[Rights] | None = element(
        tag="rights", ns="", default_factory=list
    )
    capability: (
        list[
            SODASync
            | SODAAsync
            | VOSICapabilities
            | VOSIAvailability
            | Capability
        ]
        | None
    ) = element(tag="capability", default_factory=list)


class RegistryOrganisation(
    Organisation, tag="Resource", nsmap=_RESOURCE_NSMAP, ns="ri"
):
    """Organisation serialized as:
    ``<ri:Resource xsi:type="vr:Organisation">``.
    We override the base ``Organisation`` because the vo_models implementation
    does not include the xsi:type attribute, which is required for
    registry resources.
    """

    type: Literal["vr:Organisation"] = attr(
        ns="xsi", default="vr:Organisation"
    )
