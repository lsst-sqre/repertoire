:og:description: Learn how to configure the IVOA publishing registry.

########################
IVOA publishing registry
########################

The standard for advertising services and data collections in the IVOA protocol world is a Registry.
There are two types of registries: a publishing registry, which publishes records about the services and data collections available at one site, and a searchable registry, which provides a search interface (via TAP) over registry records to find data collections and services of interest.

Repertoire has support for acting as an IVOA publishing registry.
This requires some additional configuration attached to datasets and to data services.

.. _ivoa-registry:

IVOA registry configuration
===========================

To enable IVOA publishing registry support, set ``config.ivoaRegistry`` in the Repertoire configuration.
It takes the following keys:

``adminEmail`` (required)
    Email address of the registry administrator.

``authority`` (required)
    The root IVOID for the authority publishing these records.

``ivoid`` (required)
    The IVOID for the publishing registry itself.

``created`` (required)
    The date and time at which this registry was first published, as an ISO datetime string.
    This should be set when the configuration is first added and then never changed.

``organisation`` (required)
    Organizational information for the publisher of this registry.
    This has the following keys:

    ``created`` (required)
        The date and time at which this organizational record was first published, as an ISO datetime string.
        This should be set when the configuration is first added and then never changed again.

    ``description`` (required)
        A description of the organization publishing this registry.

    ``homepage`` (required)
        A URL to the home page for this organization.

    ``ivoid`` (required)
        The IVOID of this organization.

    ``title`` (required)
        The name of the organization publishing this registry.

``creator`` (required)
    Name of the creator of this registry.

``rights`` (required)
    Freeform data rights statement for the data and services contained in this registry.

``rightsUri`` (required)
    URI to the rights statement for the data and services contained in this registry.

``repositoryName`` (required)
    The name of the publishing registry itself, not the name of the data or services contained in it.

``shortName`` (required)
    The short name of the publishing registry.
    This should be one or two words.

``subjects`` (optional)
    Default subject keywords.
    These are added to all published service records.
    Individual services can add additional keywords but not remove keywords included in this default set.

``facilities`` (optional)
    Default facility names.
    These can be overridden by individual service records.

Here is an example:

.. code-block:: yaml

   ivoaRegistry:
     adminEmail: "registry@example.com"
     authority: "ivo://org.exaple"
     created: "2026-05-20T00:00:00"
     creator: "Example Observatory"
     ivoid: "ivo://org.example/registry"
     repositoryName: "Example IVOA Publishing Registry"
     rights: >-
       Restricted to authorized data rights holders. See
       https://example.org/content/data-rights
     rightsUri: "https://example.org/content/data-rights"
     shortName: "Example"
     subjects:
       - "surveys"
       - "wide-band photometry"
     facilities:
       - "Example:Telescope"
     organisation:
       created: "2026-05-20T00:00:00Z"
       description: >-
         The Example Observatory takes pictures of the sky.
       homepage: "https://example.org"
       ivoid: "ivo://org.example/org"
       title: "Example Observatory"

.. _ivoa-dataset:

Dataset configuration
=====================

Add an ``ivoaRegistry`` entry to each dataset that should be published in the IVOA registry.
The following keys are supported:

``ivoid`` (required)
    The IVOID for this data collection.

``created`` (required)
    The date and time at which this data collection was first published, as an ISO datetime string.
    This should be set when the configuration is first added and then never changed.

``title`` (required)
    A short (one line, preferrably less than 40 characters) description of this dataset.

``description`` (required)
    A full description of this dataset.

``docsUrl`` (optional)
    A URL to further documentation about this dataset.

``subjects`` (optional)
    Additional subject keywords to add to this record.
    These are appended to the global defaults set in :ref:`ivoa-registry`.

``facilities`` (optional)
    Observatory facility names for this dataset.
    If set, it overrides the global defaults set in :ref:`ivoa-registry`.

``instruments`` (optional)
    Instrument names associated with this dataset.

Here is an example:

.. code-block:: yaml

   ivoaRegistry:
     ivoid: "ivo://org.example/dp1/datasets"
     title: "Example DP1 Datasets"
     created: "2026-05-20T00:00:00"
     description: >-
       Dataset collection for Data Preview 1, serving as the resolvable
       registry target for per-object IVOIDs referencing Butler datasets
       and HiPS surveys from this data release.

Service configuration
=====================

Only data services can be published in the IVOA publishing registry, since only data services are considered user-facing by Repertoire.
Internal services and UI services are ignored.
IVOA publishing registry details are added as an ``ivoaRegistry`` key in the rule for the data service.

All ``ivoaRegistry`` keys except those for the SODA service take, at a minimum, the same keys as the dataset entry described in :ref:`ivoa-dataset`, plus the ``ivoaServiceType`` key naming the type of service.

Only specific IVOA services known to Repertoire can be included in the publishing registry, since the registry requirements can be very service-specific.
Publishing records for new IVOA service types will require Repertoire source changes.

Group membership service (GMS)
------------------------------

No additional parameters over the base parameters.
``ivoaServiceType`` must be ``gms``.

Example:

.. code-block:: yaml

   ivoaRegistry:
     ivoaServiceType: "gms"
     ivoid: "ivo://org.example/groups"
     title: "Example Observatory GMS"
     created: '2026-06-04T00:00:00'
     description: "Group Membership Service for Example."

SIA
---

The top-level ``ivoaRegistry`` entry must contain only two keys: ``ivoaServiceType`` must be ``sia``, and ``records`` must contain an entry per dataset.

``records`` (required)
    The top-level keys must be the dataset labels for each dataset for which this service publishes an IVOA publishing registry entry.
    The values for each keys should be the normal keys for an IVOA registry entry as described in :ref:`ivoa-dataset`.

Example:

.. code-block:: yaml

   ivoaRegistry:
     ivoaServiceType: "sia"
     records:
       dp1:
         ivoid: "ivo://org.example/dp1/sia"
         title: "Example SIA Service (DP1)"
         created: "2026-05-20T00:00:00"
         description: >-
           Simple Image Access v2 service for Data Preview 1, providing
           image access to commissioning data from Rubin Observatory.

SODA
----

No additional parameters over the base parameters.
``ivoaServiceType`` must be ``soda``.

Example:

.. code-block:: yaml

   ivoaRegistry:
     ivoaServiceType: "soda"
     ivoid: "ivo://org.example/cutout"
     title: "Example Image Cutout Service"
     created: "2026-05-20T00:00:00"
     description: >-
       Image cutout service (SODA) for Example, supporting both
       synchronous and asynchronous image cutout requests.

TAP
---

The TAP entries are the most complex.
``ivoaServiceType`` must be ``tap``.
In addition to the standard parameters, the following additional parameters are supported:

``adqlVersion`` (optional)
    The version of ADQL supported by this TAP service.
    The default if this key is not provided is 2.1.

``uploadSupported`` (optional)
    Set to false if this TAP service does not support table uploads.
    The default value is true.

``additionalOutputFormats`` (optional)
    A list of additional output formats supported by this TAP server.
    This is a list of values.
    Each entry has the following keys:

    ``mime`` (required)
        The MIME type of this output format.
        This can be provided in the ``FORMAT`` parameter to select this output type.

    ``alias`` (optional)
        A list of additional aliases for this output format supported in the ``FORMAT`` parameter.

``datasets`` (required)
    A mapping of dataset labels to additional metadata for the TAP service for that dataset.
    These are used to construct the ``vs:CatalogResource`` records.
    The keys of each entry are the standard IVOA registry metadata keys as described in :ref:`ivoa-dataset`.

Example:

.. code-block:: yaml

   ivoaRegistry:
     ivoaServiceType: "tap"
     ivoid: "ivo://org.example/qserv-tap"
     title: "Example TAP Service"
     created: "2026-05-20T00:00:00"
     description: >-
       Table Access Protocol service providing access to catalog data
       from data releases.
     adqlVersion: "2.0"
     uploadSupported: true
     additionalOutputFormats:
       - mime: "application/vnd.apache.parquet"
         alias:
           - "parquet"
     datasets:
       dp1:
         ivoid: "ivo://org.example/dp1/catalogs"
         title: "Example TAP (DP1)"
         created: "2026-05-20T00:00:00"
         description: >-
           DP1 catalog data accessible via the TAP service.
         instruments:
           - "ExampleCam"
