"""OAI-PMH handler for the IVOA publishing registry.

Implements the six OAI-PMH 2.0 verbs (``Identify``, ``ListMetadataFormats``,
``ListSets``, ``ListIdentifiers``, ``ListRecords``, ``GetRecord``) required by
the IVOA Registry Interface standard.  All responses are wrapped in the
standard OAI-PMH XML response.
"""

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import UTC, datetime
from typing import cast

from lxml import etree
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from vo_models.voregistry.models import Registry
from vo_models.voresource.models import Resource

from repertoire.config import RegistryConfig
from repertoire.registry.constants import (
    IVO_MANAGED_SET,
    IVO_MANAGED_SET_NAME,
    IVO_VOR_NAMESPACE,
    IVO_VOR_PREFIX,
    IVO_VOR_SCHEMA,
    OAI_DC_NS,
    OAI_DC_PREFIX,
    OAI_DC_SCHEMA,
    OAI_DELETED_RECORD_POLICY,
    OAI_ERRORS,
    OAI_GRANULARITY,
    OAI_NS,
    OAI_SCHEMA,
    SUPPORTED_PREFIXES,
    XSI_NS,
)
from repertoire.registry.oai_models import (
    OaiDc,
    OaiDescription,
    OaiHeader,
    OaiIdentify,
    OaiListIdentifiers,
    OaiListMetadataFormats,
    OaiListSets,
    OaiMetadataFormat,
    OaiRequest,
    OaiSet,
)
from repertoire.registry.store import RecordStore


@dataclass(frozen=True)
class VerbSpec:
    """Legal arguments for one OAI-PMH verb.

    Parameters
    ----------
    required
        Arguments that must be present. Absence is a ``badArgument`` error.
    optional
        Arguments that may optionally be present.  Any argument not in
        ``required | optional | {"verb"}`` is forbidden for this verb and
        also produces a ``badArgument`` error.
    """

    required: frozenset[str] = dataclass_field(default_factory=frozenset)
    optional: frozenset[str] = dataclass_field(default_factory=frozenset)


# Map of OAI-PMH query parameter names to OaiParameters field names.
_FIELD_MAP: dict[str, str] = {
    "identifier": "identifier",
    "metadataPrefix": "metadata_prefix",
    "from": "from_",
    "until": "until",
    "set": "set_",
}

# Map of available verbs to the according VerbSpecs
_VERB_SPECS: dict[str, VerbSpec] = {
    "Identify": VerbSpec(),
    "ListSets": VerbSpec(),
    "ListMetadataFormats": VerbSpec(optional=frozenset({"identifier"})),
    "ListIdentifiers": VerbSpec(
        required=frozenset({"metadataPrefix"}),
        optional=frozenset({"from", "until", "set"}),
    ),
    "ListRecords": VerbSpec(
        required=frozenset({"metadataPrefix"}),
        optional=frozenset({"from", "until", "set"}),
    ),
    "GetRecord": VerbSpec(
        required=frozenset({"identifier", "metadataPrefix"})
    ),
}

_mapped_args = frozenset(_FIELD_MAP)
for _spec in _VERB_SPECS.values():
    for _arg in _spec.required | _spec.optional:
        if _arg not in _mapped_args:
            raise ValueError(
                f"_FIELD_MAP is missing an entry for OAI arg '{_arg}'"
            )


class OaiParameters(BaseModel):
    """Parameters for OAI-PMH requests.

    All fields are optional.  Required args enforcement is
    done by ``OaiHandler.handle`` against ``_VERB_SPECS``, not by Pydantic,
    because the required set differs per verb. Also, OAI-PMH
    requires HTTP 200 with a ``badArgument`` response when required parameters
    are missing, so we can't let Pydantic raise a ValidationError.

    Parameters
    ----------
    from_
        OAI-PMH ``from`` date for filtering records by updated datestamp.
    has_duplicate_params
        Set by the request handler when any query-parameter key appears more
        than once.  OAI-PMH treats repeated parameters as ``badArgument``.
    identifier
        OAI-PMH record identifier (IVOID), used for ``GetRecord`` and
        ``ListMetadataFormats``.
    metadata_prefix
        OAI-PMH metadata prefix - Must be one of the values in
        ``SUPPORTED_PREFIXES`` for all verbs that accept it.
    provided_args
        The set of query-parameter keys actually present in the request.
        Used by argument validation to detect forbidden arguments.
    set_
        OAI-PMH set specification - Must be ``ivo_managed`` if supplied.
    until
        OAI-PMH ``until`` date for filtering records by updated datestamp.
    verb
        OAI-PMH verb, used for building the ``<request>`` element and for
        dispatching to the appropriate handler.
    """

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    from_: str | None = Field(None, alias="from")
    has_duplicate_params: bool = Field(False, exclude=True)
    identifier: str | None = None
    metadata_prefix: str | None = None
    provided_args: frozenset[str] = Field(
        default_factory=frozenset, exclude=True
    )
    set_: str | None = Field(None, alias="set")
    until: str | None = None
    verb: str | None = None


class OaiHandler:
    """Handler for OAI-PMH requests against the IVOA publishing registry.

    Builds OAI-PMH XML responses from the in-memory record store.

    Parameters
    ----------
    store
        Immutable store of pre-built VOResource records keyed by IVOID.
    base_url
        Absolute URL of the OAI-PMH endpoint, used as the ``<baseURL>`` and
        ``<request>`` element text in every response.
    registry_config
        Registry configuration supplying the repository name, admin email,
        and organisation details.
    """

    def __init__(
        self,
        store: RecordStore,
        base_url: str,
        registry_config: RegistryConfig,
    ) -> None:
        self._store = store
        self._base_url = base_url
        self._registry_config = registry_config

    def _element_to_xml(self, root: etree._Element) -> str:
        """Serialise an lxml element tree to a UTF-8 XML string."""
        return etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8",
        ).decode()

    def _format_oai_date(self, dt: datetime) -> str:
        """Format a datetime as an OAI-PMH ``YYYY-MM-DDThh:mm:ssZ`` string."""
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _build_envelope(
        self, params: OaiParameters | None = None
    ) -> etree._Element:
        """Build the lxml OAI-PMH response envelope.

        Returns an ``<OAI-PMH>`` root element with the ``<responseDate>`` and
        ``<request>`` children populated.  All verb handlers append their
        payload into the returned element.
        """
        root = etree.Element(
            f"{{{OAI_NS}}}OAI-PMH", nsmap={None: OAI_NS, "xsi": XSI_NS}
        )
        root.set(f"{{{XSI_NS}}}schemaLocation", OAI_SCHEMA)
        etree.SubElement(
            root, f"{{{OAI_NS}}}responseDate"
        ).text = self._format_oai_date(datetime.now(UTC))
        request = OaiRequest(
            value=self._base_url,
            **(
                {
                    "verb": params.verb,
                    "identifier": params.identifier,
                    "metadata_prefix": params.metadata_prefix,
                    "from_": params.from_,
                    "until": params.until,
                    "set_": params.set_,
                }
                if params is not None
                else {}
            ),
        )
        root.append(etree.fromstring(request.to_xml(exclude_none=True)))
        return root

    def _build_header(self, root: etree._Element, record: Resource) -> None:
        """Append an OAI-PMH ``<header>`` element to ``root``."""
        header = OaiHeader(
            identifier=str(record.identifier),
            datestamp=self._format_oai_date(record.updated),
            set_spec=IVO_MANAGED_SET,
        )
        root.append(etree.fromstring(header.to_xml()))

    def _build_error(
        self,
        code: str,
        params: OaiParameters | None = None,
        *,
        detail: str | None = None,
    ) -> str:
        """Build a complete OAI-PMH error response.

        Parameters
        ----------
        code
            OAI-PMH error code (e.g. ``"badVerb"``, ``"idDoesNotExist"``).
            Must be a key in `OAI_ERRORS`.
        params
            Original request parameters.  Pass ``None`` for ``badVerb``
            errors, where the ``<request>`` element must have no attributes.
        detail
            Human-readable explanation that overrides the generic
            ``OAI_ERRORS`` message, giving more context about why the error
            occurred (e.g. which argument was missing or unrecognised).

        Returns
        -------
        str
            Serialised OAI-PMH XML error response.
        """
        root = self._build_envelope(None if code == "badVerb" else params)
        error_el = etree.SubElement(root, f"{{{OAI_NS}}}error")
        error_el.set("code", code)
        error_el.text = (
            detail
            if detail is not None
            else OAI_ERRORS.get(code, "Unknown error")
        )
        return self._element_to_xml(root)

    def _create_oai_dc(self, record: Resource) -> OaiDc:
        """Create an OAI Dublin Core record for a VOResource record.

        Parameters
        ----------
        record
            Record to serialise as Dublin Core.

        Returns
        -------
        OaiDc
            Dublin Core record populated from the VOResource metadata.
        """
        return OaiDc(
            title=record.title or None,
            identifier=str(record.identifier),
            description=(
                record.content.description
                if record.content and record.content.description
                else None
            ),
            subject=list(record.content.subject or [])
            if record.content
            else [],
            publisher=(
                record.curation.publisher.value
                if record.curation and record.curation.publisher
                else None
            ),
            type_=getattr(record, "type", None),
            date=self._format_oai_date(record.updated),
        )

    def _append_metadata(
        self, parent: etree._Element, record: Resource, metadata_prefix: str
    ) -> None:
        """Append a ``<metadata>`` element to ``parent``.

        VOResource records are serialised via their own ``to_xml()`` and
        combined with ``etree.fromstring`` because pydantic-xml cannot
        express a union field over cross-namespace vo_models types at class
        definition time.
        """
        metadata = etree.SubElement(parent, f"{{{OAI_NS}}}metadata")
        if metadata_prefix == OAI_DC_PREFIX:
            metadata.append(
                etree.fromstring(
                    self._create_oai_dc(record).to_xml(exclude_none=True)
                )
            )
        else:
            metadata.append(
                etree.fromstring(
                    record.to_xml(skip_empty=True, exclude_none=True)
                )
            )

    def _build_record_element(
        self, parent: etree._Element, record: Resource, metadata_prefix: str
    ) -> None:
        """Append a complete OAI-PMH ``<record>`` element to ``parent``."""
        record_el = etree.SubElement(parent, f"{{{OAI_NS}}}record")
        self._build_header(record_el, record)
        self._append_metadata(record_el, record, metadata_prefix)

    def _check_identifier(self, params: OaiParameters) -> str | None:
        """Return an ``idDoesNotExist`` error if ``params.identifier`` is set
        but not found in the store, or ``None`` if the identifier is absent or
        valid.

        Parameters
        ----------
        params
            OAI-PMH request parameters.

        Returns
        -------
        str | None
            A serialised error response, or ``None`` if no error.
        """
        if (
            params.identifier is not None
            and self._store.get(params.identifier) is None
        ):
            return self._build_error(
                "idDoesNotExist",
                params,
                detail=(
                    f"No record found with identifier '{params.identifier}'."
                ),
            )
        return None

    def _validate_arguments(
        self, params: OaiParameters, spec: VerbSpec
    ) -> str | None:
        """Validate request arguments against the spec for the requested verb.

        Checks in order: no forbidden arguments, all required arguments
        present, ``metadataPrefix`` is a recognised format, ``set`` is a
        recognised set, ``from``/``until`` are valid datestamps.

        Parameters
        ----------
        params
            Parsed OAI-PMH request parameters.
        spec
            Argument specification for the requested verb.

        Returns
        -------
        str | None
            A serialised OAI-PMH error response if validation fails, or
            ``None`` if all arguments are valid.
        """
        allowed_params = {"verb"}.union(spec.required, spec.optional)
        unexpected_params = params.provided_args - allowed_params
        if unexpected_params:
            arg = next(iter(sorted(unexpected_params)))
            return self._build_error(
                "badArgument",
                params,
                detail=(
                    f"The '{arg}' argument is not allowed for {params.verb}."
                ),
            )

        for oai_name in spec.required:
            if not getattr(params, _FIELD_MAP[oai_name]):
                return self._build_error(
                    "badArgument",
                    params,
                    detail=(
                        f"The '{oai_name}' argument is required for"
                        f" {params.verb}."
                    ),
                )

        if (
            params.metadata_prefix is not None
            and params.metadata_prefix not in SUPPORTED_PREFIXES
        ):
            return self._build_error(
                "cannotDisseminateFormat",
                params,
                detail=(
                    f"Metadata format '{params.metadata_prefix}' is not"
                    f" supported. Supported formats:"
                    f" {', '.join(SUPPORTED_PREFIXES)}."
                ),
            )

        if params.set_ and params.set_ != IVO_MANAGED_SET:
            return self._build_error(
                "noRecordsMatch",
                params,
                detail=(
                    f"Set '{params.set_}' is not recognised. The only"
                    f" supported set is '{IVO_MANAGED_SET}'."
                ),
            )

        if "from" in spec.optional or "until" in spec.optional:
            if error := self._validate_date_params(params):
                return error

        return None

    def _validate_date_params(self, params: OaiParameters) -> str | None:
        """Validate ``from`` and ``until`` date arguments.

        Checks that each supplied date string is a valid datestamp,
        that both use the same granularity when both are present, and that
        ``from`` is not later than ``until``.

        Parameters
        ----------
        params
            OAI-PMH request parameters to check.

        Returns
        -------
        str | None
            A serialised ``badArgument`` error response if the dates are
            invalid, or ``None`` if they are acceptable.
        """

        def _granularity(s: str) -> str:
            return "datetime" if "T" in s else "date"

        def _parse(s: str) -> datetime | None:
            try:
                return datetime.fromisoformat(s)
            except ValueError:
                return None

        if params.from_ and _parse(params.from_) is None:
            return self._build_error(
                "badArgument",
                params,
                detail=f"Invalid date format for 'from': '{params.from_}'.",
            )

        if params.until and _parse(params.until) is None:
            return self._build_error(
                "badArgument",
                params,
                detail=f"Invalid date format for 'until': '{params.until}'.",
            )

        if params.from_ and params.until:
            if _granularity(params.from_) != _granularity(params.until):
                return self._build_error(
                    "badArgument",
                    params,
                    detail=(
                        "The 'from' and 'until' arguments must use the same"
                        " date granularity."
                    ),
                )
            from_dt, until_dt = _parse(params.from_), _parse(params.until)
            if from_dt and until_dt and from_dt > until_dt:
                return self._build_error(
                    "badArgument",
                    params,
                    detail="The 'from' date must not be later than 'until'.",
                )

        return None

    def _filter_records(
        self, records: list[Resource], params: OaiParameters
    ) -> list[Resource]:
        """Filter records by the ``from``/``until`` date range in params.

        Assumes date params have already been validated by
        ``_validate_date_params``.

        Parameters
        ----------
        records
            Records to filter.
        params
            OAI-PMH request parameters supplying the date bounds.

        Returns
        -------
        list[Resource]
            Records whose ``updated`` datestamp falls within the range.
        """
        if params.from_:
            from_dt = datetime.fromisoformat(params.from_)
            if from_dt.tzinfo is None:
                from_dt = from_dt.replace(tzinfo=UTC)
            records = [r for r in records if r.updated >= from_dt]

        if params.until:
            until_dt = datetime.fromisoformat(params.until)
            if until_dt.tzinfo is None:
                until_dt = until_dt.replace(tzinfo=UTC)
            records = [r for r in records if r.updated <= until_dt]

        return records

    def _handle_identify(self, params: OaiParameters) -> str:
        """Handle an ``Identify`` request.

        Returns repository metadata (name, base URL, admin
        email etc) and embeds the registry's own VOResource record in a
        ``<description>`` element.

        Parameters
        ----------
        params
            Parsed OAI-PMH request parameters.

        Returns
        -------
        str
            Serialised OAI-PMH XML response containing an ``<Identify>``
            element.
        """
        earliest = self._store.earliest_datestamp()
        _record = self._store.get(str(self._registry_config.ivoid))
        registry_record = _record if isinstance(_record, Registry) else None
        root = self._build_envelope(params)
        identify = OaiIdentify(
            repository_name=self._registry_config.repository_name,
            base_url=self._base_url,
            protocol_version="2.0",
            admin_email=self._registry_config.admin_email,
            earliest_datestamp=(
                self._format_oai_date(earliest)
                if earliest
                else "1970-01-01T00:00:00Z"
            ),
            deleted_record=OAI_DELETED_RECORD_POLICY,
            granularity=OAI_GRANULARITY,
            description=(
                OaiDescription(registry=registry_record)
                if registry_record is not None
                else None
            ),
        )
        root.append(etree.fromstring(identify.to_xml(exclude_none=True)))
        return self._element_to_xml(root)

    def _handle_list_metadata_formats(self, params: OaiParameters) -> str:
        """Handle a ``ListMetadataFormats`` request.

        Returns the two metadata formats supported by this registry:
        ``ivo_vor`` (full VOResource XML) and ``oai_dc`` (Dublin Core).
        If an ``identifier`` argument is supplied, checks that the record
        exists before listing formats (All records support both formats).

        Parameters
        ----------
        params
            Parsed OAI-PMH request parameters.

        Returns
        -------
        str
            Serialised OAI-PMH XML response containing a
            ``<ListMetadataFormats>`` element, or an ``idDoesNotExist``
            error if the identifier is not found.
        """
        if error := self._check_identifier(params):
            return error
        root = self._build_envelope(params)
        formats = OaiListMetadataFormats(
            formats=[
                OaiMetadataFormat(
                    metadata_prefix=IVO_VOR_PREFIX,
                    schema_url=IVO_VOR_SCHEMA,
                    metadata_namespace=IVO_VOR_NAMESPACE,
                ),
                OaiMetadataFormat(
                    metadata_prefix=OAI_DC_PREFIX,
                    schema_url=OAI_DC_SCHEMA,
                    metadata_namespace=OAI_DC_NS,
                ),
            ]
        )
        root.append(etree.fromstring(formats.to_xml(exclude_none=True)))
        return self._element_to_xml(root)

    def _handle_list_sets(self, params: OaiParameters) -> str:
        """Handle a ``ListSets`` request.

        Returns the single set this registry exposes: ``ivo_managed``.

        Parameters
        ----------
        params
            Parsed OAI-PMH request parameters.

        Returns
        -------
        str
            Serialised OAI-PMH XML response containing a ``<ListSets>``
            element.
        """
        root = self._build_envelope(params)
        sets = OaiListSets(
            sets=[
                OaiSet(set_spec=IVO_MANAGED_SET, set_name=IVO_MANAGED_SET_NAME)
            ]
        )
        root.append(etree.fromstring(sets.to_xml(exclude_none=True)))
        return self._element_to_xml(root)

    def _handle_list_identifiers(self, params: OaiParameters) -> str:
        """Handle a ``ListIdentifiers`` request.

        Returns record headers (identifier, datestamp, set membership) for
        all records, optionally filtered by the ``from``/``until`` date
        range. Returns ``noRecordsMatch`` if the date filter excludes
        everything.

        Parameters
        ----------
        params
            Parsed OAI-PMH request parameters.

        Returns
        -------
        str
            Serialised OAI-PMH XML response containing a
            ``<ListIdentifiers>`` element, or a ``noRecordsMatch`` error.
        """
        records = self._filter_records(self._store.all(), params)
        if not records:
            return self._build_error("noRecordsMatch", params)
        root = self._build_envelope(params)
        identifiers = OaiListIdentifiers(
            headers=[
                OaiHeader(
                    identifier=str(r.identifier),
                    datestamp=self._format_oai_date(r.updated),
                    set_spec=IVO_MANAGED_SET,
                )
                for r in records
            ]
        )
        root.append(etree.fromstring(identifiers.to_xml(exclude_none=True)))
        return self._element_to_xml(root)

    def _handle_list_records(self, params: OaiParameters) -> str:
        """Handle a ``ListRecords`` request.

        Returns full records (header + metadata) for all records,
        optionally filtered by the ``from``/``until`` date range.
        Each record's metadata is serialised in the format requested by
        ``metadataPrefix`` (``ivo_vor`` or ``oai_dc``). Returns
        ``noRecordsMatch`` if the date filter excludes everything.

        Parameters
        ----------
        params
            Parsed OAI-PMH request parameters.

        Returns
        -------
        str
            Serialised OAI-PMH XML response containing a
            ``<ListRecords>`` element, or a ``noRecordsMatch`` error.
        """
        metadata_prefix = cast("str", params.metadata_prefix)
        records = self._filter_records(self._store.all(), params)
        if not records:
            return self._build_error("noRecordsMatch", params)
        root = self._build_envelope(params)
        list_records = etree.SubElement(root, f"{{{OAI_NS}}}ListRecords")
        for record in records:
            self._build_record_element(list_records, record, metadata_prefix)
        return self._element_to_xml(root)

    def _handle_get_record(self, params: OaiParameters) -> str:
        """Handle a ``GetRecord`` request.

        Returns the full record (header + metadata) for the single
        identifier supplied.
        Returns ``idDoesNotExist`` if the identifier is not found.

        Parameters
        ----------
        params
            Parsed OAI-PMH request parameters.

        Returns
        -------
        str
            Serialised OAI-PMH XML response containing a ``<GetRecord>``
            element, or an ``idDoesNotExist`` error.
        """
        metadata_prefix = cast("str", params.metadata_prefix)

        if not params.identifier:
            return self._build_error(
                "badArgument",
                params,
                detail="The 'identifier' argument is required for GetRecord.",
            )
        record = self._store.get(params.identifier)
        if record is None:
            return self._build_error(
                "idDoesNotExist",
                params,
                detail=(
                    f"No record found with identifier '{params.identifier}'."
                ),
            )
        root = self._build_envelope(params)
        get_record = etree.SubElement(root, f"{{{OAI_NS}}}GetRecord")
        self._build_record_element(get_record, record, metadata_prefix)
        return self._element_to_xml(root)

    def handle(self, params: OaiParameters) -> str:
        """Dispatch an OAI-PMH request to the appropriate verb handler.

        Validates arguments against ``_VERB_SPECS`` before dispatching.
        All responses (including errors) use HTTP 200 as required by the
        OAI-PMH spec.

        Parameters
        ----------
        params
            Parsed OAI-PMH request parameters extracted from the query string.

        Returns
        -------
        str
            Serialised OAI-PMH XML response.
        """
        if params.has_duplicate_params:
            return self._build_error(
                "badArgument",
                params,
                detail="Repeated query parameters are not permitted.",
            )

        spec = (
            _VERB_SPECS.get(params.verb) if params.verb is not None else None
        )
        if spec is None:
            return self._build_error("badVerb")

        if error := self._validate_arguments(params, spec):
            return error

        match params.verb:
            case "Identify":
                return self._handle_identify(params)
            case "ListMetadataFormats":
                return self._handle_list_metadata_formats(params)
            case "ListIdentifiers":
                return self._handle_list_identifiers(params)
            case "ListRecords":
                return self._handle_list_records(params)
            case "ListSets":
                return self._handle_list_sets(params)
            case "GetRecord":
                return self._handle_get_record(params)
            case _:
                raise RuntimeError(
                    f"Verb '{params.verb}' is in _VERB_SPECS but has no"
                    " handler - update the match statement in handle()."
                )
