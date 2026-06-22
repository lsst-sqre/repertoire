"""Factory for building IVOA VOResource records from discovery data."""

from datetime import datetime
from typing import Literal

from pydantic import AnyUrl, TypeAdapter
from structlog import BoundLogger
from vo_models.tapregext.models import (
    Language,
    OutputFormat,
    TableAccess,
    UploadMethod,
    Version,
)
from vo_models.vodataservice.models import ParamHTTP
from vo_models.voregistry.models import OAIHTTP, Authority, Harvest, Registry
from vo_models.voresource.models import (
    AccessURL,
    Capability,
    Contact,
    Content,
    Creator,
    Curation,
    Relationship,
    Resource,
    ResourceName,
    Rights,
    Service,
)

from repertoire.config import RegistryConfig
from repertoire.registry.constants import (
    TAP_OUTPUT_FORMAT_MIME,
    TAP_UPLOAD_ID,
    VO_SUBJECT,
)
from repertoire.registry.models import (
    CatalogResource,
    GroupMembershipService,
    PlainService,
    RegistryOrganisation,
    SimpleImageAccess,
    SODAAsync,
    SODASync,
    TapAux,
    TypedService,
    VOSIAvailability,
    VOSICapabilities,
    VOSITables,
)
from repertoire.registry.store import RecordStore
from rubin.repertoire import (
    ApiVersion,
    BaseRegistryEntry,
    DataService,
    Discovery,
    GmsRegistryEntry,
    IvoaStandardId,
    SiaDatasetRegistryEntry,
    SodaRegistryEntry,
    TapRegistryEntry,
)


class ResourceRecordFactory:
    """Factory for creating IVOA VOResource records.

    Records are built once from the registry configuration and the
    pre-rendered discovery data. The ``startup_timestamp`` is recorded as the
    ``updated`` datestamp on every record.

    Parameters
    ----------
    registry_config
        IVOA publishing registry configuration.
    discovery
        Pre-rendered discovery data containing resolved service URLs and
        standard IDs.
    startup_timestamp
        Timestamp captured at application startup, used as the ``updated``
        datestamp on all records.
    oai_url
        Absolute URL of the OAI-PMH endpoint, used as the access URL in the
        ``vg:Harvest`` capability of the registry record.
    logger
        Logger for recording any warnings or errors during record creation.
    """

    def __init__(
        self,
        registry_config: RegistryConfig,
        discovery: Discovery,
        startup_timestamp: datetime,
        oai_url: str,
        logger: BoundLogger,
    ) -> None:
        self._registry_config = registry_config
        self._discovery = discovery
        self._startup_timestamp = startup_timestamp
        self._oai_url: AnyUrl = TypeAdapter(AnyUrl).validate_python(oai_url)
        self._curation = self._create_curation()
        self._logger = logger

    def _create_registry(self) -> Registry:
        """Create the vg:Registry record describing this publishing registry.

        Returns
        -------
        Registry
            Registry record with a vg:Harvest capability pointing to the
            OAI-PMH endpoint.
        """
        authority_id = str(self._registry_config.authority).removeprefix(
            "ivo://"
        )
        return Registry(
            created=self._registry_config.created,
            updated=self._startup_timestamp,
            status="active",
            title=self._registry_config.repository_name,
            short_name=self._registry_config.short_name,
            identifier=self._registry_config.ivoid,
            curation=self._curation,
            content=Content(
                subject=VO_SUBJECT,
                description=self._registry_config.organisation.description,
                reference_url=self._registry_config.organisation.homepage,
            ),
            capability=[
                Harvest(
                    interface=[
                        OAIHTTP(
                            access_url=[
                                AccessURL(
                                    value=self._oai_url,
                                    use="base",
                                )
                            ],
                            role="std",
                        )
                    ],
                    max_records=0,
                )
            ],
            full=False,
            managed_authority=[authority_id],
        )

    def _create_curation(self) -> Curation:
        """Create the curation block shared by all records.

        Returns
        -------
        Curation
            Curation block with the organisation as publisher and contact.
        """
        return Curation(
            publisher=ResourceName(
                value=self._registry_config.organisation.title
            ),
            creator=[
                Creator(name=ResourceName(value=self._registry_config.creator))
            ],
            contact=[
                Contact(
                    name=ResourceName(
                        value=self._registry_config.organisation.title
                    ),
                    email=self._registry_config.admin_email,
                )
            ],
        )

    def _create_interface(
        self, url: AnyUrl, *, use: Literal["full", "base", "dir"] = "base"
    ) -> ParamHTTP:
        """Create a ParamHTTP interface for a given access URL.

        Parameters
        ----------
        url
            The access URL for the service endpoint.
        use
            Access URL ``use`` attribute: ``"base"`` for prefix-matching
            endpoints (e.g. TAP, VOSI tables) or ``"full"`` for exact-match
            endpoints (e.g. VOSI capabilities, VOSI availability).

        Returns
        -------
        ParamHTTP
            A ParamHTTP interface with the given URL.
        """
        return ParamHTTP(
            access_url=[AccessURL(value=url, use=use)],
            role="std",
        )

    def _create_authority(self) -> Authority:
        """Create the IVOA authority record for this publishing registry.

        Returns
        -------
        Authority
            Authority record identifying this registry's IVOA authority.
        """
        return Authority(
            created=self._registry_config.created,
            updated=self._startup_timestamp,
            status="active",
            title=self._registry_config.repository_name,
            identifier=self._registry_config.authority,
            curation=self._curation,
            content=Content(
                subject=VO_SUBJECT,
                description=self._registry_config.organisation.description,
                reference_url=self._registry_config.organisation.homepage,
            ),
            managing_org=ResourceName(
                ivo_id=str(self._registry_config.organisation.ivoid),
            ),
        )

    def _create_organisation(self) -> RegistryOrganisation:
        """Create the IVOA organisation record for Rubin Observatory.

        Returns
        -------
        Organisation
            Organisation record describing the publishing institution.
        """
        return RegistryOrganisation(
            created=self._registry_config.organisation.created,
            updated=self._startup_timestamp,
            status="active",
            title=self._registry_config.organisation.title,
            identifier=self._registry_config.organisation.ivoid,
            curation=self._curation,
            content=Content(
                subject=VO_SUBJECT,
                description=self._registry_config.organisation.description,
                reference_url=self._registry_config.organisation.homepage,
            ),
        )

    def _create_gms(
        self, api_version: ApiVersion, registry: GmsRegistryEntry
    ) -> Service:
        """Create a GMS record for a Group Membership Service.

        One record is created for the service as a whole.

        Parameters
        ----------
        api_version
            Service discovery information for the GMS IVOA standard ID.
        registry
            The IVOA registry entry containing the IVOID, title, and
            datestamps.

        Returns
        -------
        Service
            A Service record for the GMS API.
        """
        interface = self._create_interface(api_version.url)
        return PlainService(
            created=registry.created,
            updated=self._startup_timestamp,
            status="active",
            title=registry.title,
            identifier=registry.ivoid,
            curation=self._curation,
            content=Content(
                subject=VO_SUBJECT,
                description=registry.description,
                reference_url=(
                    registry.docs_url
                    or self._registry_config.organisation.homepage
                ),
            ),
            rights=[
                Rights(
                    value=self._registry_config.rights,
                    rights_uri=self._registry_config.rights_uri,
                )
            ],
            capability=[GroupMembershipService(interface=[interface])],
        )

    def _create_tap(
        self, service: DataService, registry: TapRegistryEntry
    ) -> Service:
        """Create a TAPRegExt service record for a TAP endpoint.

        Parameters
        ----------
        service
            The discovered service corresponding to this registry record.
        registry
            The TAP registry entry containing the IVOID, title, datestamps,
            and TAP-specific fields.

        Returns
        -------
        Service
            A Service record with a TableAccess capability as well as
            tables, capabilities, and availability endpoints.
        """
        url = service.url
        base = str(url).rstrip("/")

        return TypedService(
            created=registry.created,
            updated=self._startup_timestamp,
            status="active",
            title=registry.title,
            identifier=registry.ivoid,
            curation=self._curation,
            content=Content(
                subject=VO_SUBJECT,
                description=registry.description,
                reference_url=(
                    registry.docs_url
                    or self._registry_config.organisation.homepage
                ),
            ),
            rights=[
                Rights(
                    value=self._registry_config.rights,
                    rights_uri=self._registry_config.rights_uri,
                )
            ],
            capability=[
                TableAccess(
                    interface=[self._create_interface(url)],
                    language=[
                        Language(
                            name="ADQL",
                            version=[Version(value=registry.adql_version)],
                            language_features=None,
                        )
                    ],
                    output_format=[OutputFormat(mime=TAP_OUTPUT_FORMAT_MIME)],
                    upload_method=(
                        [UploadMethod(ivo_id=TAP_UPLOAD_ID)]
                        if registry.upload_supported
                        else None
                    ),
                ),
                VOSICapabilities(
                    interface=[
                        self._create_interface(
                            TypeAdapter(AnyUrl).validate_python(
                                f"{base}/capabilities"
                            ),
                            use="full",
                        )
                    ]
                ),
                VOSIAvailability(
                    interface=[
                        self._create_interface(
                            TypeAdapter(AnyUrl).validate_python(
                                f"{base}/availability"
                            ),
                            use="full",
                        )
                    ]
                ),
                VOSITables(
                    interface=[
                        self._create_interface(
                            TypeAdapter(AnyUrl).validate_python(
                                f"{base}/tables"
                            ),
                        )
                    ]
                ),
            ],
        )

    def _create_soda(
        self, service: DataService, registry: SodaRegistryEntry
    ) -> Service:
        """Create a SODA service record for an image cutout endpoint.

        One record is created for the service as a whole, with separate
        capabilities for the synchronous and asynchronous endpoints.

        Parameters
        ----------
        service
            The discovered service corresponding to this registry record.
        registry
            The IVOA registry entry containing the IVOID, title, and
            datestamps.

        Returns
        -------
        Service
            A Service record with capabilities for each SODA version.
        """
        capabilities: list[Capability] = []
        async_version = service.version_for_id(IvoaStandardId.SODA_ASYNC_1)
        if async_version:
            interface = self._create_interface(async_version.url)
            capabilities.append(SODAAsync(interface=[interface]))
        sync_version = service.version_for_id(IvoaStandardId.SODA_SYNC_1)
        if sync_version:
            interface = self._create_interface(sync_version.url)
            capabilities.append(SODASync(interface=[interface]))

        return TypedService(
            created=registry.created,
            updated=self._startup_timestamp,
            status="active",
            title=registry.title,
            identifier=registry.ivoid,
            curation=self._curation,
            content=Content(
                subject=VO_SUBJECT,
                description=registry.description,
                reference_url=(
                    registry.docs_url
                    or self._registry_config.organisation.homepage
                ),
            ),
            rights=[
                Rights(
                    value=self._registry_config.rights,
                    rights_uri=self._registry_config.rights_uri,
                )
            ],
            capability=capabilities,
        )

    def _create_sia(
        self,
        api_version: ApiVersion,
        registry: SiaDatasetRegistryEntry,
    ) -> Service:
        """Create an SIAv2 service record for a per-collection image access
        endpoint.

        Parameters
        ----------
        api_version
            Service discovery information for the SIAv2 IVOA standard ID.
        registry
            The dataset registry entry for this specific dataset.

        Returns
        -------
        Service
            A Service record with an SIA capability for this dataset.
        """
        interface = self._create_interface(api_version.url)
        return TypedService(
            created=registry.created,
            updated=self._startup_timestamp,
            status="active",
            title=registry.title,
            identifier=registry.ivoid,
            curation=self._curation,
            content=Content(
                subject=VO_SUBJECT,
                description=registry.description,
                reference_url=(
                    registry.docs_url
                    or self._registry_config.organisation.homepage
                ),
            ),
            rights=[
                Rights(
                    value=self._registry_config.rights,
                    rights_uri=self._registry_config.rights_uri,
                )
            ],
            capability=[SimpleImageAccess(interface=[interface])],
        )

    def _create_tap_catalog_resource(
        self,
        service: DataService,
        tap_registry: TapRegistryEntry,
        entry: BaseRegistryEntry,
    ) -> CatalogResource:
        """Create a TAPRegExt catalog resource record for a TAP endpoint.

        Parameters
        ----------
        service
            The discovered service corresponding to this registry record.
        tap_registry
            The registry entry containing the TAP-specific fields.
        entry
            The base registry entry containing the IVOID, title, datestamps,
            and description for the catalog resource.

        Returns
        -------
        CatalogResource
            A CatalogResource record.
        """
        return CatalogResource(
            created=entry.created,
            updated=self._startup_timestamp,
            status="active",
            title=entry.title,
            identifier=entry.ivoid,
            curation=self._curation,
            content=Content(
                subject=VO_SUBJECT,
                description=entry.description,
                reference_url=(
                    entry.docs_url
                    or self._registry_config.organisation.homepage
                ),
                relationship=[
                    Relationship(
                        relationship_type="IsServedBy",
                        related_resource=[
                            ResourceName(ivo_id=str(tap_registry.ivoid))
                        ],
                    )
                ],
            ),
            rights=[
                Rights(
                    value=self._registry_config.rights,
                    rights_uri=self._registry_config.rights_uri,
                )
            ],
            capability=[
                TapAux(interface=[self._create_interface(service.url)])
            ],
        )

    def _add_service_record(
        self,
        records: dict[str, Resource],
        dataset: str,
        name: str,
        service: DataService,
    ) -> None:
        """Add a registry record for this service if IVOA registry is set."""
        registry = service.ivoa_registry
        if registry is None:
            return

        ivoid = str(registry.ivoid)
        if ivoid in records:
            self._logger.debug(
                "Skipping duplicate registry record",
                dataset=dataset,
                service=name,
                ivoid=ivoid,
            )
            return

        kind = None
        match registry:
            case GmsRegistryEntry():
                version = service.version_for_id(IvoaStandardId.GMS_SEARCH_1)
                if version:
                    records[ivoid] = self._create_gms(version, registry)
                    kind = "GMS"
            case SiaDatasetRegistryEntry():
                version = service.version_for_id(IvoaStandardId.SIA_QUERY_2)
                if version:
                    records[ivoid] = self._create_sia(version, registry)
                    kind = "SIA"
            case SodaRegistryEntry():
                records[ivoid] = self._create_soda(service, registry)
                kind = "SODA"
            case TapRegistryEntry():
                records[ivoid] = self._create_tap(service, registry)
                kind = "TAP"

        if kind:
            self._logger.debug(
                f"Created {kind} record for discovered service",
                dataset=dataset,
                service=name,
                ivoid=ivoid,
            )

    def _add_tap_catalog_resource(
        self,
        records: dict[str, Resource],
        dataset: str,
        service: DataService,
    ) -> None:
        """Add a Catalog Resource record for this dataset if the service is
        TAP.
        """
        if not isinstance(service.ivoa_registry, TapRegistryEntry):
            return
        entry = service.ivoa_registry.records.get(dataset)
        if entry is None:
            return
        ivoid = str(entry.ivoid)
        if ivoid in records:
            self._logger.debug(
                "Skipping duplicate TAP CatalogResource record",
                dataset=dataset,
                ivoid=ivoid,
            )
            return
        records[ivoid] = self._create_tap_catalog_resource(
            service, service.ivoa_registry, entry
        )
        self._logger.debug(
            "Created TAP CatalogResource record for discovered service",
            dataset=dataset,
            ivoid=ivoid,
        )

    def create_all(self) -> RecordStore:
        """Create all VOResource records and return them as a RecordStore.

        Iterates over discovered dataset services and dispatches to the
        appropriate record builder based on the ``ivoa_registry`` entry.

        Returns
        -------
        RecordStore
            Store of all built records keyed by IVOID.
        """
        records: dict[str, Resource] = {
            str(self._registry_config.ivoid): self._create_registry(),
            str(self._registry_config.authority): self._create_authority(),
            str(self._registry_config.organisation.ivoid): (
                self._create_organisation()
            ),
        }

        for dataset, dataset_info in self._discovery.datasets.items():
            for name, service in dataset_info.services.items():
                self._add_service_record(records, dataset, name, service)
                self._add_tap_catalog_resource(records, dataset, service)

        return RecordStore(records=records)
