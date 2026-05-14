"""pydantic-xml models for the OAI-PMH 2.0 protocol."""

from pydantic_xml import BaseXmlModel, attr, element
from vo_models.voregistry.models import Registry

__all__ = [
    "OaiDc",
    "OaiDescription",
    "OaiError",
    "OaiHeader",
    "OaiIdentify",
    "OaiListIdentifiers",
    "OaiListMetadataFormats",
    "OaiListSets",
    "OaiMetadataFormat",
    "OaiRequest",
    "OaiSet",
]

_OAI_NS = "http://www.openarchives.org/OAI/2.0/"
_XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
_DC_NS = "http://purl.org/dc/elements/1.1/"
_OAI_DC_NS = "http://www.openarchives.org/OAI/2.0/oai_dc/"

_OAI_DC_NSMAP = {
    "oai_dc": _OAI_DC_NS,
    "dc": _DC_NS,
    "xsi": _XSI_NS,
}

_OAI_DC_SCHEMA_LOCATION = (
    f"{_OAI_DC_NS} http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
)


class OaiRequest(BaseXmlModel, tag="request", ns=_OAI_NS):
    """The ``<request>`` element present in every OAI-PMH response."""

    verb: str | None = attr(default=None)
    identifier: str | None = attr(default=None)
    metadata_prefix: str | None = attr(name="metadataPrefix", default=None)
    from_: str | None = attr(name="from", default=None)
    until: str | None = attr(default=None)
    set_: str | None = attr(name="set", default=None)
    value: str | None = None


class OaiError(BaseXmlModel, tag="error", ns=_OAI_NS):
    """An ``<error>`` element in an OAI-PMH error response."""

    code: str = attr()
    value: str | None = None


class OaiHeader(BaseXmlModel, tag="header", ns=_OAI_NS):
    """An OAI-PMH ``<header>`` element identifying a single record."""

    identifier: str = element(tag="identifier", ns=_OAI_NS)
    datestamp: str = element(tag="datestamp", ns=_OAI_NS)
    set_spec: str = element(tag="setSpec", ns=_OAI_NS)


class OaiMetadataFormat(BaseXmlModel, tag="metadataFormat", ns=_OAI_NS):
    """A ``<metadataFormat>`` entry within ``<ListMetadataFormats>``."""

    metadata_prefix: str = element(tag="metadataPrefix", ns=_OAI_NS)
    schema_url: str = element(tag="schema", ns=_OAI_NS)
    metadata_namespace: str = element(tag="metadataNamespace", ns=_OAI_NS)


class OaiSet(BaseXmlModel, tag="set", ns=_OAI_NS):
    """An ``<set>`` entry within``<ListSets>``."""

    set_spec: str = element(tag="setSpec", ns=_OAI_NS)
    set_name: str = element(tag="setName", ns=_OAI_NS)


class OaiDescription(BaseXmlModel, tag="description", ns=_OAI_NS):
    """A ``<description>`` element embedding a VOResource registry record."""

    registry: Registry


class OaiIdentify(BaseXmlModel, tag="Identify", ns=_OAI_NS):
    """The ``<Identify>`` payload returned for the ``Identify`` verb."""

    repository_name: str = element(tag="repositoryName", ns=_OAI_NS)
    base_url: str = element(tag="baseURL", ns=_OAI_NS)
    protocol_version: str = element(tag="protocolVersion", ns=_OAI_NS)
    admin_email: str = element(tag="adminEmail", ns=_OAI_NS)
    earliest_datestamp: str = element(tag="earliestDatestamp", ns=_OAI_NS)
    deleted_record: str = element(tag="deletedRecord", ns=_OAI_NS)
    granularity: str = element(tag="granularity", ns=_OAI_NS)
    description: OaiDescription | None = element(
        tag="description", ns=_OAI_NS, default=None
    )


class OaiListMetadataFormats(
    BaseXmlModel, tag="ListMetadataFormats", ns=_OAI_NS
):
    """The ``<ListMetadataFormats>`` payload."""

    formats: list[OaiMetadataFormat] = element(
        tag="metadataFormat", ns=_OAI_NS, default_factory=list
    )


class OaiListSets(BaseXmlModel, tag="ListSets", ns=_OAI_NS):
    """The ``<ListSets>`` payload."""

    sets: list[OaiSet] = element(tag="set", ns=_OAI_NS, default_factory=list)


class OaiListIdentifiers(BaseXmlModel, tag="ListIdentifiers", ns=_OAI_NS):
    """The ``<ListIdentifiers>`` payload."""

    headers: list[OaiHeader] = element(
        tag="header", ns=_OAI_NS, default_factory=list
    )


class OaiDc(BaseXmlModel, tag="dc", ns="oai_dc", nsmap=_OAI_DC_NSMAP):
    """An ``<oai_dc:dc>`` Dublin Core metadata record."""

    schema_location: str = attr(
        name="schemaLocation",
        ns="xsi",
        default=_OAI_DC_SCHEMA_LOCATION,
    )
    title: str | None = element(tag="title", ns="dc", default=None)
    identifier: str | None = element(tag="identifier", ns="dc", default=None)
    description: str | None = element(tag="description", ns="dc", default=None)
    subject: list[str] = element(tag="subject", ns="dc", default_factory=list)
    publisher: str | None = element(tag="publisher", ns="dc", default=None)
    type_: str | None = element(tag="type", ns="dc", default=None)
    date: str | None = element(tag="date", ns="dc", default=None)
