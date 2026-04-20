"""Factory for building IVOA VOResource records from Repertoire config."""

from datetime import datetime

from pydantic import AnyUrl, HttpUrl
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

from repertoire.config import Config, RegistryConfig
from repertoire.registry.constants import (
    SODA_ASYNC_STANDARD_ID,
    SODA_SYNC_STANDARD_ID,
    TAP_OUTPUT_FORMAT_MIME,
    TAP_UPLOAD_ID,
    VO_SUBJECT,
    anyurl,
)
from repertoire.registry.models import SimpleImageAccess, SODAAsync, SODASync
from repertoire.registry.store import RecordStore
from rubin.repertoire import (
    ApiService,
    DataServiceRule,
    DatasetRegistryEntry,
    Discovery,
    IvoaRegistryEntry,
    MultiRecordRegistryEntry,
    TapRegistryConfig,
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
        registry_config = config.registry
        if registry_config is None:
            raise ValueError("Registry configuration is required")
        self._registry_config: RegistryConfig = registry_config
        self._discovery = discovery
        self._startup_timestamp = startup_timestamp
        self._oai_url = oai_url
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
        authority_id = self._registry_config.authority.removeprefix("ivo://")
        return Registry(
            created=self._registry_config.created,
            updated=self._startup_timestamp,
            status="active",
            title=self._registry_config.repository_name,
            identifier=anyurl.validate_python(self._registry_config.ivoid),
            curation=self._curation,
            content=Content(
                subject=VO_SUBJECT,
                description=self._registry_config.organisation.description,
                reference_url=anyurl.validate_python(
                    self._registry_config.organisation.homepage
                ),
            ),
            capability=[
                Harvest(
                    interface=[
                        OAIHTTP(
                            access_url=[
                                AccessURL(
                                    value=anyurl.validate_python(
                                        self._oai_url
                                    ),
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

    def _create_interface(self, url: AnyUrl | str) -> ParamHTTP:
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
            access_url=[
                AccessURL(value=anyurl.validate_python(str(url)), use="base")
            ],
            role="std",
        )

    @staticmethod
    def _resolve_url(rule: DataServiceRule, service: ApiService) -> HttpUrl:
        """Return the access URL for a service.

        Parameters
        ----------
        rule
            The data service rule, which may pin a specific API version.
        service
            The resolved service from discovery data.

        Returns
        -------
        HttpUrl
            The access URL for the service or its pinned version.
        """
        if rule.versions:
            version_key = next(iter(rule.versions))
            return service.versions[version_key].url
        return service.url

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
            identifier=anyurl.validate_python(self._registry_config.authority),
            curation=self._curation,
            content=Content(
                subject=VO_SUBJECT,
                description=self._registry_config.organisation.description,
                reference_url=anyurl.validate_python(
                    self._registry_config.organisation.homepage
                ),
            ),
            managing_org=ResourceName(
                ivo_id=self._registry_config.organisation.ivoid,
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
            identifier=anyurl.validate_python(
                self._registry_config.organisation.ivoid
            ),
            curation=self._curation,
            content=Content(
                subject=VO_SUBJECT,
                description=self._registry_config.organisation.description,
                reference_url=anyurl.validate_python(
                    self._registry_config.organisation.homepage
                ),
            ),
        )

    def _create_tap(
        self,
        rule: DataServiceRule,
        registry: IvoaRegistryEntry,
        tap: TapRegistryConfig,
    ) -> Service:
        """Create a TAPRegExt service record for a TAP endpoint.

        Parameters
        ----------
        rule
            The data service rule for this TAP service. Only the first dataset
            in ``rule.datasets`` is used.
        registry
            The IVOA registry entry containing the IVOID, title, and
            datestamps.
        tap
            TAP-specific configuration including ADQL version and upload
            support.

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
        url = self._resolve_url(rule, service)

        return Service(
            created=registry.created,
            updated=self._startup_timestamp,
            status="active",
            title=registry.title,
            identifier=anyurl.validate_python(registry.ivoid),
            curation=self._curation,
            content=Content(
                subject=VO_SUBJECT,
                description=registry.description,
                reference_url=anyurl.validate_python(
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
                            version=[Version(value=tap.adql_version)],
                            language_features=None,
                        )
                    ],
                    output_format=[OutputFormat(mime=TAP_OUTPUT_FORMAT_MIME)],
                    upload_method=(
                        [UploadMethod(ivo_id=TAP_UPLOAD_ID)]
                        if tap.upload_supported
                        else None
                    ),
                )
            ],
        )

    def _create_soda(
        self,
        rule: DataServiceRule,
        registry: IvoaRegistryEntry,
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
            A Service record with capabilities for each SODA endpoint version.
        """
        if not rule.datasets:
            raise RuntimeError(
                f"_create_soda called for rule '{rule.name}' with no datasets"
            )
        dataset = next(iter(rule.datasets))
        service = self._discovery.datasets[dataset].services[rule.name]
        capabilities: list[Capability] = []
        for api_version in service.versions.values():
            if api_version.ivoa_standard_id == SODA_SYNC_STANDARD_ID:
                capabilities.append(
                    SODASync(
                        interface=[self._create_interface(api_version.url)]
                    )
                )
            elif api_version.ivoa_standard_id == SODA_ASYNC_STANDARD_ID:
                capabilities.append(
                    SODAAsync(
                        interface=[self._create_interface(api_version.url)]
                    )
                )
            else:
                raise RuntimeError(
                    f"Unrecognised SODA standard ID"
                    f" '{api_version.ivoa_standard_id}'"
                    f" for service '{rule.name}'"
                )
        return Service(
            created=registry.created,
            updated=self._startup_timestamp,
            status="active",
            title=registry.title,
            identifier=anyurl.validate_python(registry.ivoid),
            curation=self._curation,
            content=Content(
                subject=VO_SUBJECT,
                description=registry.description,
                reference_url=anyurl.validate_python(
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
        url = self._resolve_url(rule, service)

        return Service(
            created=registry.created,
            updated=self._startup_timestamp,
            status="active",
            title=registry.title,
            identifier=anyurl.validate_python(registry.ivoid),
            curation=self._curation,
            content=Content(
                subject=VO_SUBJECT,
                description=registry.description,
                reference_url=anyurl.validate_python(
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

    def _validate_soda_standard_ids(
        self, rule: DataServiceRule, dataset: str, service: ApiService
    ) -> None:
        """Check that a SODA service has both sync and async standard IDs.

        Parameters
        ----------
        rule
            The data service rule being validated.
        dataset
            The dataset name, used in error messages.
        service
            The resolved service from discovery data.

        Raises
        ------
        ValueError
            If either sync or async standard ID is missing.
        """
        standard_ids = {
            v.ivoa_standard_id
            for v in service.versions.values()
            if v.ivoa_standard_id
        }
        missing = {
            SODA_SYNC_STANDARD_ID,
            SODA_ASYNC_STANDARD_ID,
        } - standard_ids
        if missing:
            raise ValueError(
                f"SODA service '{rule.name}' for dataset"
                f" '{dataset}' is missing standard ID(s):"
                f" {', '.join(sorted(missing))}"
            )

    def _validate_dataset(self, rule: DataServiceRule, dataset: str) -> None:
        """Validate one dataset entry for a service rule.

        Parameters
        ----------
        rule
            The data service rule being validated.
        dataset
            The dataset name to validate.

        Raises
        ------
        ValueError
            If the dataset or service is missing, or if standard IDs are
            absent where required.
        """
        if dataset not in self._discovery.datasets:
            raise ValueError(
                f"Dataset '{dataset}' in rule '{rule.name}'"
                " not found in discovery data"
            )
        service = self._discovery.datasets[dataset].services.get(rule.name)
        if not service:
            raise ValueError(
                f"Service '{rule.name}' for dataset"
                f" '{dataset}' not found in discovery data"
            )
        if rule.registry is None:
            return
        service_type = rule.registry.ivoa_service_type
        if service_type != "tap":
            for version_key, api_version in service.versions.items():
                if not api_version.ivoa_standard_id:
                    raise ValueError(
                        f"API version '{version_key}' for"
                        f" service '{rule.name}' in dataset"
                        f" '{dataset}' is missing an IVOA"
                        " standard ID in discovery data"
                    )
        if service_type == "soda":
            self._validate_soda_standard_ids(rule, dataset, service)

    def _validate(self) -> None:
        """Validate the configuration and discovery data before creating
        records.

        Checks that all service rules have corresponding discovery entries with
        resolved URLs and standard IDs.

        Raises
        ------
        ValueError
            If any service rule references a dataset, service, API version, or
            standard ID that is not found in the discovery data.
        """
        for rule_list in self._config.rules.values():
            for rule in rule_list:
                if not isinstance(rule, DataServiceRule):
                    continue
                if rule.registry is None:
                    continue
                for dataset in rule.datasets or []:
                    self._validate_dataset(rule, dataset)

    def create_all(self) -> RecordStore:
        """Create all VOResource records and return them as a RecordStore.

        Iterates over all service rules in the configuration. Rules with a
        ``tap`` key produce TAPRegExt records, rules with a flat
        ``registry`` entry produce SODA records and rules with a dict
        ``registry`` entry produce one SIA record per dataset.

        Returns
        -------
        RecordStore
            Store of all built records keyed by IVOID.
        """
        self._validate()
        records: dict[str, Resource] = {}
        records[self._registry_config.ivoid] = self._create_registry()
        records[self._registry_config.authority] = self._create_authority()
        records[self._registry_config.organisation.ivoid] = (
            self._create_organisation()
        )

        for rule_list in self._config.rules.values():
            for rule in rule_list:
                if not isinstance(rule, DataServiceRule):
                    continue
                if rule.registry is None or not rule.datasets:
                    continue

                service_type = rule.registry.ivoa_service_type

                if service_type == "tap" and isinstance(
                    rule.registry, IvoaRegistryEntry
                ):
                    if rule.tap is None:
                        raise ValueError(
                            f"TAP rule '{rule.name}' is missing a"
                            " 'tap:' config block"
                        )
                    records[rule.registry.ivoid] = self._create_tap(
                        rule, rule.registry, rule.tap
                    )
                    self._logger.info(
                        "Created TAP record for rule", rule=rule.name
                    )

                elif service_type == "soda" and isinstance(
                    rule.registry, IvoaRegistryEntry
                ):
                    records[rule.registry.ivoid] = self._create_soda(
                        rule, rule.registry
                    )
                    self._logger.info(
                        "Created SODA record for rule", rule=rule.name
                    )

                elif service_type == "sia" and isinstance(
                    rule.registry, MultiRecordRegistryEntry
                ):
                    for dataset, entry in rule.registry.records.items():
                        records[entry.ivoid] = self._create_sia(
                            rule, dataset, entry
                        )
                        self._logger.info(
                            "Created SIA record for rule and dataset",
                            rule=rule.name,
                            dataset=dataset,
                        )

                else:
                    self._logger.warning(
                        "Rule registry entry does not match any known"
                        " record type, skipping",
                        rule=rule.name,
                    )

        return RecordStore(records=records)
