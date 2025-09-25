:og:description: Requesting service URLs from Repertoire.

.. py:currentmodule:: rubin.repertoire

################
Finding services
################

Repertoire's discovery endpoint provides the URLs of other services running in the same Phalanx environment.

Service types
=============

Services are divided into three classes:

#. Data services: REST APIs, one base URL per dataset name (although for some services all the URLs may be the same), and intended for use either by users directly or by other services.
#. UI services: browser UIs, one entry-point URL per Phalanx environment, intended for use by users or administrators.
#. Internal services: REST APIs, one base URL per Phalanx environment, used primarily (but not necessarily exclusively) by other services and not by users directly.

Service APIs
============

`DiscoveryClient` provides the following methods to look up services.
These APIs do not require authentication.

`DiscoveryClient.url_for_data`
    Takes the name of the service and the name of the dataset and returns the corresponding base URL for that service's REST API, or `None` if that service is not running in the local Phalanx environment or if it doesn't provide that dataset.
    See :doc:`datasets` for information on how to find the dataset names available in the local environment.

`DiscoveryClient.url_for_internal`
    Takes the name of the service and returns the base URL for that service's REST API, or `None` if that service is not running in the local Phalanx environment.

`DiscoveryClient.url_for_ui`
    Takes the name of the service and returns the entry-point URL for the browser-based user interface, or `None` if that service is not running in the local Phalanx environment.

URLs are returned as strings.

REST API versions
-----------------

Data and internal services may have multiple REST APIs.
These can be discovered with the following methods:

`DiscoveryClient.versions_for_data`
    Takes the name of the service and dataset and returns a list of the available versions in the local Phalanx environment.
    If the service is not versioned, the list will be empty.
    If the service is not present in the local environment or doesn't provide that dataset, the return value will be `None`.

`DiscoveryClient.versions_for_internal`
    Takes the name of the service and returns a list of the available versions in the local Phalanx environment.
    If the service is not versioned, the list will be empty.
    If the service is not present in the local environment, the return value will be `None`.

In addition, there is an optional keyword argument, ``version``, to the `~DiscoveryClient.url_for_data` and `~DiscoveryClient.url_for_internal` methods.
If provided, the method will return the URL for that specific version instead of the default URL.
The return value will be `None` if the service is not versioned or if that version is not available in the local environment.

In the case of versioned services, the default URL (returned by `~DiscoveryClient.url_for_data` and `~DiscoveryClient.url_for_internal` with no ``version`` argument) will be the base URL of the top-level REST API without any version.
When ``version`` is provided, the returned URL will be the base URL for that version of the API.

Butler configuration
====================

Configuring a client of the Butler_ service is a special case.
The base URL of the Butler service REST API is not available through the above service APIs.
The Butler client instead requires a URL to a configuration file.

Clients that need to instantiate a single Butler for a specific dataset should call `DiscoveryClient.butler_config_for` and pass in the name of a dataset.
The return value will be a URL to the Butler configuration for that dataset, or `None` if no Butler for that dataset is available.
This URL, in turn, can be used to the ``Butler`` constructor.

Clients that need to handle all available datasets and create a Butler on the fly for each request should call `DiscoveryClient.butler_repositories` and pass the result into the constructor of ``LabeledButlerFactory``.
The resulting factory can then be used to create Butler instances for labels as needed.

Next steps
==========

- Query for datasets: :doc:`datasets`
- Query for Phalanx applications: :doc:`applications`
