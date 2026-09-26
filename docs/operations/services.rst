:og:description: Learn how to configure discovery rules for services.

#############
Service rules
#############

Services are defined in Repertoire using service rules, which map the name of a Phalanx application to one more more services provided by that application that should be registered with service discovery.
In any given Phalanx environment, Repertoire will filter the service rules down to those corresponding to datasets and Phalanx applications deployed in that environment, and then use those rules to generate service discovery entries for each service.

Service rules are primarily configured via the ``config.rules`` Helm setting.
Some additional details are configured via ``config.subdomainOverrides``.
The HiPS service is a special case discussed in :doc:`hips`.

Normally, all rules should be added to the ``config.rules`` setting in :file:`applications/repertoire/values.yaml` in Phalanx.
It is possible to add rules directly in :file:`applications/repertoire/values-{environment}.yaml` for a specific environment, but this pattern is discouraged since applications are rarely deployed in only one environment.
Instead, add the rules to the main :file:`values.yaml` file; the rule will be ignored if that application is not deployed in a given environment.

Service types
=============

Services are classified as one of three types:

data
    A user-facing API service to retrieve or process information from a specific dataset.
    The base URL for the service may vary based on the dataset.
    This type of service is used for all user-facing services even if their URLs currently do not vary based on dataset.
    This will allow us to provide different endpoints for different datasets in the future if we need to for backwards compatibility reasons.

internal
    An internal API service used mostly by other services and not tied to any particular dataset.
    Users are not expected to send requests to internal services directly.

ui
    A service that provides a web-based user interface intended to be accessed via a web browser.
    UI services may be user-facing or only for administrators.

Anatomy of a rule
=================

Here is an example service discovery rule for the Phalanx application `gafaelfawr <https://phalanx.lsst.io/applications/gafaelfawr/>`__:

.. code-block:: yaml

   gafaelfawr:
     data:
       gms:
         title: "Group membership service (GMS)"
         template: "https://{{base_hostname}}/auth/gms"
         docsUrl: "https://www.ivoa.net/documents/GMS/"
         versions:
           gms-search-1.0:
             template: "https://{{base_hostname}}/auth/gms"
             ivoaStandardId: "ivo://ivoa.net/std/gms#search-1.0"
         ivoaRegistry:
           ivoaServiceType: "gms"
           ivoid: "ivo://org.rubinobs/groups"
           title: "Rubin Observatory GMS"
           created: '2026-06-04T00:00:00'
           description: "Group Membership Service for Rubin Observatory."
     internal:
       gafaelfawr:
         template: "https://{{base_hostname}}/auth"
         docsUrl: "https://gafaelfawr.lsst.io/"
         versions:
           v1:
             template: "https://{{base_hostname}}/auth/api/v1"
         openapi: "https://{{base_hostname}}/auth/openapi.json"
       login:
         title: "User login"
         template: "https://{{base_hostname}}/login"
     ui:
       logout:
         title: "User logout"
         template: "https://{{base_hostname}}/logout"

This is a single entry in the Repertoire :file:`values.yaml` entry under ``config.rules``.

The top-level key, ``gafaelfawr``, must be the name of a Phalanx application.
This rule applies to any environment in which the ``gafaelfawr`` application is enabled and is ignored in other environments.

.. warning::

   There is currently no way to write a rule that is conditional on particular settings for a Phalanx application.
   All rules for the application are processed if the application is enabled.

Below that key are sections for the three types of services: ``data``, ``internal``, and ``ui``.
A given application may register services in any of those three.
Most applications will register a single service of one type, but some applications, such as Gafaelfawr, provide multiple interfaces that need separate registrations.

Below the type of service is the service name.
This is the keyword used by clients of service discovery to find a specific service.
Note that while the service name may relate to the Phalanx application name (such as the internal ``gafaelfawr`` service), it may specify an interface provided by this Phalanx service but with an entirely different name (such as the data ``gms`` service).

Below the service name is the rule itself.
Rules for the three types of services are discussed in more detail below.

Writing a rule
==============

The following top-level keys are used by all rules:

``template`` (required)
    The only required element, this tells Repertoire how to construct the base URL for this service.
    It is a Jinja_ template with one preset variable: ``base_hostname``, which will be replaced with the base hostname of this Phalanx installation.
    Data services use an additional preset variable as documented below.

``title`` (optional)
    A short (aim for 40 characters or less) human-readable description of the service.
    Rubin documentation convention is to use sentence casing, not title casing, for headings; this should be applied to service titles as well.

``docsUrl`` (optional)
    A URL to more details about the service.
    If the service has its own documentation site, that is usually the best URL to list.
    IF not, a link to a standards document that specifies the API that the service implements may be appropriate.

``requiredScopes`` (optional)
    A list of the scopes required to access this service.
    A user must have all of the scopes listed.
    This information is not used directly by Gafaelfawr_ and must be kept in sync with the ``GafaelfawrIngress`` configuration.
    It is used by applications such as Squareone_ to determine whether to show services to a given user.
    See :dmtn:`234` for the list of scopes used by the Rubin Science Platform.

UI service rules
----------------

UI service rules are the simplest.
They only allow the top-level keys that are allowed for all rules.

For example, here is the part of the Gafaelfawr Repertoire configuration that defines the ``logout`` service, a UI service to which a user's browser can be sent to log them out of their Rubin Science Platform session.

.. code-block:: yaml

   ui:
     logout:
       title: "User logout"
       template: "https://{{base_hostname}}/logout"

Here is an example for the Nublado Notebook Aspect UI, which uses all of the allowed fields:

.. code-block:: yaml

   ui:
     nublado:
       title: "Notebook aspect"
       requiredScopes:
         - "exec:notebook"
       template: "https://{{base_hostname}}/nb"
       docsUrl: "https://nublado.lsst.io/"

API service rules
-----------------

The remaining service types, internal and data, both support some additional keys:

``openapi`` (optional)
    A URL template to generate the URL to the OpenAPI specification for this service.
    This is a Jinja_ template processed in the same way and with the same variables as ``template``.

``quotaLabels`` (optional)
    A mapping of Gafaelfawr service names that may be used for quota restrictions to information about how that quota label is used.
    Gafaelfawr service names are entirely distinct from both service discovery service names and from Phalanx application names, although by convention they either match or start with the Phalanx application name that defines that ``GafaelfawrIngress``.
    See `the Gafaelfawr documentation <https://gafaelfawr.lsst.io/user-guide/quotas.html>`__ for more details about service names and quotas.

    The supported keys under each quota label are:

    ``title`` (required)
        A short (aim for 40 characters or less) human-readable description of what a quota for this Gafaelfawr service would limit.

    ``internal`` (optional)
        If set to true, this quota label is used internally by the Rubin Science Platform and is not interesting for users.
        This quota label should be hidden from any user-facing documentation or UIs.

``versions`` (optional)
    A mapping of API versions to information about each API version.
    This key can be omitted if the service's API is not versioned; however, by convention, services that implement IVOA protocols should have ``versions`` entries for each IVOA protocol they implement.
    This key will be used by clients that need to discover a specific version of an API, rather than the base URL for the latest and most general API provided by the service.

    Under each version key, the following keys are supported:

    ``template`` (required)
        A Jinja template for the URL to this specific version of the API.
        This uses the same variables and is processed in the same way as the top-level ``template`` value.

    ``ivoaStandardId`` (optional)
        The IVOA standardID of this service, as used in ``vr:Capability`` elements within a `VOResource <https://www.ivoa.net/documents/VOResource/>`__.
        This should be present for any service API that follows an IVOA standard with a registered standardID.
        There should be one ``versions`` entry for each standardID implemented by this service, even if that means there are multiple records pointing to the same URL.
        This key is generally only used by data services, since internal services are not normally IVOA-standardized.

Internal service rules
----------------------

Internal service rules only support the general service rule keys and the additional keys for API services.
Here again is the Gafaelfawr internal service example from above, which is the entry for the internal Gafaelfawr API.

.. code-block:: yaml

   internal:
     gafaelfawr:
       title: "Gafaelfawr"
       template: "https://{{base_hostname}}/auth"
       docsUrl: "https://gafaelfawr.lsst.io/"
       versions:
         v1:
           template: "https://{{base_hostname}}/auth/api/v1"
       openapi: "https://{{base_hostname}}/auth/openapi.json"

Data service rules
------------------

Data services are services that are intended for direct use by users of the Science Platform.
All data services are tied to specific datasets.
To look up the URL for a data service, the user must specify both the dataset and the service name.

Repertoire intentionally does not support user-facing services that are not tied to a dataset.
Even for services that can serve any dataset, separate entries are published for each dataset supported in that Phalanx environment.
This ensures that, in the future, older datasets can use a different URL to a service with backward-compatibility support, which helps to enable reproducibility of results when working with older code for older datasets that may be assuming older APIs.

Data service rules support the following additional keys:

``datasets`` (optional)
    A list of datasets supported by this service.
    If this key is absent, a service discovery entry will be generated for this service for every dataset supported by the local environment.
    If it is present, the service discovery entry will only be generated for the intersection of datasets listed under this key and datasets supported by the local environment.
    If that intersection is empty, this service will not be advertised even if the corresponding Phalanx application is deployed.

``ivoaRegistry`` (optional)
    Additional metadata for the IVOA publishing registry.
    Publishing registry support is still being tested and is not yet documented.

In addition, all Jinja templates within a data service support an additional variable: ``dataset``, which is replaced with the name of the dataset for which the service discovery entry is being generated.
This allows the service to use separate URLs per dataset.

Here is an example of a data service that uses that variable:

.. code-block:: yaml

   data:
     sia:
       title: "Simple image access (SIA)"
       datasets:
         - "dp02"
         - "dp1"
         - "dp2"
       requiredScopes:
         - "read:image"
       quotaLabels:
         sia:
           title: "Image requests"
       template: "https://{{base_hostname}}/api/sia/{{dataset}}"
       versions:
         sia-query-2.0:
           template: "https://{{base_hostname}}/api/sia/{{dataset}}/query"
           ivoaStandardId: "ivo://ivoa.net/std/SIA#query-2.0"
       openapi: "https://{{base_hostname}}/api/sia/openapi.json"
       docsUrl: "https://www.ivoa.net/documents/SIA/"

Here is an example of a data service that can be used for any dataset and does not use the ``dataset`` variable in its URL templates.

.. code-block::

   gms:
     title: "Group membership service (GMS)"
     template: "https://{{base_hostname}}/auth/gms"
     docsUrl: "https://www.ivoa.net/documents/GMS/"
     versions:
       gms-search-1.0:
         template: "https://{{base_hostname}}/auth/gms"
         ivoaStandardId: "ivo://ivoa.net/std/gms#search-1.0"

Note the use of ``ivoaStandardId`` under the ``versions`` key in both examples.

Subdomain overrides
===================

Currently, most Phalanx applications register routes under the base hostname of the Phalanx environment.
In the future, some applications will be moving to subdomains in at least some environments to provide better JavaScript and web security isolation.

If an application supports running in a subdomain, also add rules for that service under ``config.subdomainOverrides``.
The entries under that key should not be full rules.
They should only include the keys that contain URL templates (such as ``template`` or ``openapi``), and should only override the templates that need to change if that application is running in a subdomain.

For example, if the Nublado Notebook Aspect is running in a subdomain, the UI is hosted on a different URL.
Here is the corresponding override rule:

.. code-block:: yaml

   subdomainOverrides:
     nublado:
       ui:
         nublado:
           template: "https://nb.{{base_hostname}}/nb"

The ``config.useSubdomains`` setting should then be overridden for each Phalanx environment that uses subdomains to list the applications running in subdomains at that environment.
Repertoire will choose whether to apply the subdomain overrides before generating a service discovery entry by checking whether the application appears in that list.
