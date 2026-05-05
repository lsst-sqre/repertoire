"""Factory for building IVOA VOResource records from Repertoire config."""

from collections.abc import Callable
from datetime import datetime
from typing import Any

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
    Curation,
    Organisation,
    Resource,
    ResourceName,
    Service,
)

from repertoire.config import Config
from repertoire.registry.constants import (
    TAP_OUTPUT_FORMAT_MIME,
    TAP_UPLOAD_ID,
    VO_SUBJECT,
)
from repertoire.registry.models import (
    SimpleImageAccess,
    SODAAsync,
    SODASync,
    TypedService,
)
from repertoire.registry.store import RecordStore
from rubin.repertoire import (
    DataServiceRule,
    DatasetRegistryEntry,
    Discovery,
    IvoaStandardId,
    SiaRegistryEntry,
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
    config
        Full Repertoire configuration, including registry config and service
        rules.
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
        config: Config,
        discovery: Discovery,
        startup_timestamp: datetime,
        oai_url: str,
        logger: BoundLogger,
    ) -> None:
        self._config = config
        if config.ivoa_registry is None:
            raise ValueError("Registry configuration is required")
        self._registry_config = config.ivoa_registry
        self._discovery = discovery
        self._startup_timestamp = startup_timestamp
        self._oai_url: AnyUrl = TypeAdapter(AnyUrl).validate_python(oai_url)
        self._curation = self._create_curation()
        self._logger = logger

    def _service(self, **kwargs: Any) -> Service:
        return TypedService(**kwargs)

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
            contact=[
                Contact(
                    name=ResourceName(
                        value=self._registry_config.organisation.title
                    ),
                    email=self._registry_config.admin_email,
                )
            ],
        )

    def _create_interface(self, url: AnyUrl) -> ParamHTTP:
        """Create a ParamHTTP interface for a given access URL.

        Parameters
        ----------
        url
            The access URL for the service endpoint.

        Returns
        -------
        ParamHTTP
            A ParamHTTP interface with the given URL as a base access URL.
        """
        return ParamHTTP(
            access_url=[AccessURL(value=url, use="base")],
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

    def _create_organisation(self) -> Organisation:
        """Create the IVOA organisation record for Rubin Observatory.

        Returns
        -------
        Organisation
            Organisation record describing the publishing institution.
        """
        return Organisation(
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

    def _create_tap(
        self,
        rule: DataServiceRule,
        registry: TapRegistryEntry,
    ) -> Service:
        """Create a TAPRegExt service record for a TAP endpoint.

        Parameters
        ----------
        rule
            The data service rule for this TAP service.
        registry
            The TAP registry entry containing the IVOID, title, datestamps,
            and TAP-specific fields.

        Returns
        -------
        Service
            A Service record with a TableAccess capability.
        """
        if not rule.datasets:
            raise RuntimeError(
                f"_create_tap called for rule '{rule.name}' with no datasets"
            )
        dataset = next(iter(rule.datasets))
        service = self._discovery.datasets[dataset].services[rule.name]
        url = service.url

        return self._service(
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
                )
            ],
        )

    def _create_soda(
        self,
        rule: DataServiceRule,
        registry: SodaRegistryEntry,
    ) -> Service:
        """Create a SODA service record for an image cutout endpoint.

        One record is created for the service as a whole, with separate
        capabilities for the synchronous and asynchronous endpoints.

        Parameters
        ----------
        rule
            The data service rule for this SODA service. Only the first dataset
            in ``rule.datasets`` is used.
        registry
            The IVOA registry entry containing the IVOID, title, and
            datestamps.

        Returns
        -------
        Service
            A Service record with capabilities for each SODA version.
        """
        if not rule.datasets:
            raise RuntimeError(
                f"_create_soda called for rule '{rule.name}' with no datasets"
            )
        dataset = next(iter(rule.datasets))
        service = self._discovery.datasets[dataset].services[rule.name]
        capabilities: list[Capability] = []
        for api_version in service.versions.values():
            match api_version.ivoa_standard_id:
                case IvoaStandardId.SODA_SYNC_1:
                    capabilities.append(
                        SODASync(
                            interface=[self._create_interface(api_version.url)]
                        )
                    )
                case IvoaStandardId.SODA_ASYNC_1:
                    capabilities.append(
                        SODAAsync(
                            interface=[self._create_interface(api_version.url)]
                        )
                    )
                case _:
                    raise RuntimeError(
                        f"Unrecognised SODA standard ID"
                        f" '{api_version.ivoa_standard_id}'"
                        f" for service '{rule.name}'"
                    )
        return self._service(
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
            capability=capabilities,
        )

    def _create_sia(
        self,
        rule: DataServiceRule,
        dataset: str,
        registry: DatasetRegistryEntry,
    ) -> Service:
        """Create an SIAv2 service record for a per-collection image access
        endpoint.

        Parameters
        ----------
        rule
            The data service rule for this SIA service.
        dataset
            The dataset name this record is for (e.g. ``dp1``, ``dp02``).
        registry
            The dataset registry entry for this specific dataset.

        Returns
        -------
        Service
            A Service record with an SIA capability for this dataset.
        """
        service = self._discovery.datasets[dataset].services[rule.name]
        sia_version = next(
            v
            for v in service.versions.values()
            if v.ivoa_standard_id == IvoaStandardId.SIA_QUERY_2
        )
        url = sia_version.url

        return self._service(
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
            capability=[
                SimpleImageAccess(
                    interface=[self._create_interface(url)],
                )
            ],
        )

    def _is_discoverable(self, rule: DataServiceRule, dataset: str) -> bool:
        return (
            dataset in self._discovery.datasets
            and rule.name in self._discovery.datasets[dataset].services
        )

    def _handle_single_dataset(
        self,
        rule: DataServiceRule,
        registry: TapRegistryEntry | SodaRegistryEntry,
        records: dict[str, Resource],
        builder: Callable[[DataServiceRule, Any], Resource],
        kind: str,
    ) -> None:
        """Handle TAP and SODA rules, which create one record per rule with
        a single dataset.

        Parameters
        ----------
        rule
            The data service rule being processed.
        registry
            The IVOA registry entry for this rule.
        records
            The dictionary of records being built, to add the new record to.
        builder
            The method to call to build the record (e.g. ``_create_tap``)
        kind
            A str describing the kind of record being created (for logging).

        Returns
        -------
        None
        """
        if not rule.datasets:
            self._logger.debug(
                "Rule has no datasets, skipping",
                rule=rule.name,
            )
            return
        dataset = next(iter(rule.datasets))
        if not self._is_discoverable(rule, dataset):
            return

        records[str(registry.ivoid)] = builder(rule, registry)
        self._logger.debug(
            f"Created {kind} record for rule",
            rule=rule.name,
        )

    def _handle_sia(
        self,
        rule: DataServiceRule,
        registry: SiaRegistryEntry,
        records: dict[str, Resource],
    ) -> None:
        """Handle SIA rules, which create one record per dataset in the rule.

        Parameters
        ----------
        rule
            The data service rule being processed.
        registry
            The IVOA registry entry for this rule.
        records
            The dictionary of records being built.

        Returns
        -------
        None
        """
        for dataset, entry in registry.records.items():
            if not self._is_discoverable(rule, dataset):
                continue
            records[str(entry.ivoid)] = self._create_sia(rule, dataset, entry)
            self._logger.debug(
                "Created SIA record for rule and dataset",
                rule=rule.name,
                dataset=dataset,
            )

    def _process_rule(
        self, rule: DataServiceRule, records: dict[str, Resource]
    ) -> None:
        """Process one service rule from the configuration, creating
        VOResource records.

        Parameters
        ----------
        rule
            The data service rule to process.
        records
            The dictionary of records being built.

        Returns
        -------
        None
        """
        if rule.ivoa_registry is None or not rule.datasets:
            return

        registry = rule.ivoa_registry

        if isinstance(registry, TapRegistryEntry):
            self._handle_single_dataset(
                rule, registry, records, self._create_tap, "TAP"
            )
        elif isinstance(registry, SodaRegistryEntry):
            self._handle_single_dataset(
                rule, registry, records, self._create_soda, "SODA"
            )
        elif isinstance(registry, SiaRegistryEntry):
            self._handle_sia(rule, registry, records)

    def create_all(self) -> RecordStore:
        """Create all VOResource records and return them as a RecordStore.

        Iterates over all service rules in the configuration and dispatches
        to the appropriate record builder based on the type of the
        ``ivoa_registry`` entry.

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

        for rule_list in self._config.rules.values():
            for rule in rule_list:
                if isinstance(rule, DataServiceRule):
                    self._process_rule(rule, records)

        return RecordStore(records=records)
