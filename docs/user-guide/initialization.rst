:og:description: Learn how to initialize the Repertoire client.

.. py:currentmodule:: rubin.repertoire

############################
Creating a Repertoire client
############################

Users of Repertoire can obtain a client via either a FastAPI dependency or a simple call to the constructor.
However, some Phalanx configuration for the client is required first.

.. _client-phalanx:

Phalanx configuration for Repertoire
====================================

The URL for the local Repertoire service will be obtained from the ``REPERTOIRE_BASE_URL`` environment variable.
This, in turn, should be injected into the client's environment via Phalanx, using the Phalanx ``global.repertoireUrl`` Helm variable, which is created by Argo CD.

If this environment variable is not set, the `DiscoveryClient` constructor will raise `RepertoireUrlError`.

Older applications whose Helm charts were created before Repertoire will not be configured to inject either this Helm setting or this environment variable.
See the Phalanx documentation on `adding Repertoire support <https://phalanx.lsst.io/developers/add-repertoire.html>`__ if you are adding Repertoire support to an older application.

.. _client-dependency:

Use the FastAPI dependency
==========================

If the client is a FastAPI application, it's usually easiest to use the provided FastAPI dependency.
This maintains a singleton process-global Repertoire client that shares an HTTP connection pool with the Safir `~safir.dependencies.http_client.http_client_dependency`.

When using this dependency in an application that uses structlog_, call `~DiscoveryDependency.initialize` to set the logger used for service discovery to the application's configured structlog logger:

.. code-block:: python

   import structlog
   from rubin.repertoire import discovery_dependency


   # ... initialize logger (probably with configure_logging) ...
   logger = structlog.get_logger("<application>")
   discovery_dependency.initialize(logger)

This should be done during application startup, before any of its routes are accessed.

Then, import the Repertoire dependency and include it in the parameters to whatever route needs to do service discovery:

.. code-block:: python

   from fastapi import Depends
   from rubin.repertoire import discovery_dependency
   from typing import Annotated


   @router.get("/something")
   async def handle_something(
       dataset: str,
       *,
       discovery: Annotated[DiscoveryClient, Depends(discovery_dependency)],
   ) -> SomeModel:
       cutout_url = discovery.url_for_data("cutout-sync", dataset)
       # ...do something with the URL...

This dependency uses `~safir.dependencies.http_client.http_client_dependency` under the hood, so you should insert a call to ``http_client_depnedency.aclose()`` in the cleanup portion of your application's FastAPI lifespan callback.
See `the Safir documentation <https://safir.lsst.io/user-guide/http-client.html>`__ for more details.

Manually create a client
========================

Most users of Repertoire can create a client with a simple call to the constructor of `DiscoveryClient`:

.. code-block:: python

   from rubin.repertoire import DiscoveryClient


   discovery = DiscoveryClient()

This requires the ``REPERTOIRE_BASE_URL`` environment variable be set to the base URL of the Repertoire service, which is normally arranged via :ref:`Phalanx configuration <client-phalanx>`.

When you are done using the client, call `DiscoveryClient.aclose` to clean up the internal HTTP pool.

Provide a structlog logger
--------------------------

Users of Repertoire that use structlog_ should provide their configured structlog logger to the Repertoire client.

.. code-block:: python

   from rubin.repertoire import DiscoveryClient
   from structlog.stdlib import get_logger


   logger = get_logger("service")
   discovery = DiscoveryClient(logger=logger)

This will provide formatted and level-appropriate logging of actions taken by the Repertoire client.

If a logger is not provided, `DiscoveryClient` will use a default structlog logger, which may not have the desired configuration.

Override the base URL
---------------------

If the client knows the base URL for the Repertoire REST API via some other mechanism, it can override the base URL with a constructor paramter to `DiscoveryClient`:

.. code-block:: python

   from rubin.repertoire import DiscoveryClient


   discovery = DiscoveryClient(base_url="https://example.com/repertoire")

In this case, the environment variable is ignored and may be unset.

Provide an HTTPX client
-----------------------

By default, Repertoire creates a new HTTPX_ client.
This is slightly wasteful if the application already has an HTTPX client, since it will create a new connection pool.

To use an existing HTTPX ``AsyncClient`` for making requests to Repertoire, pass it in as the first argument to the `DiscoveryClient` constructor:

.. code-block:: python

   from httpx import AsyncClient
   from rubin.repertoire import DiscoveryClient


   client = AsyncClient()
   discovery = DiscoveryClient(client)

This is also the pattern to use if the Repertoire client needs custom HTTPX configuration for whatever reason, such as custom timeouts or special headers.
That configuration can be added to the HTTPX client before passing it into the `DiscoveryClient` constructor.

If you provide an HTTPX client, you do not need to call `DiscoveryClient.aclose`.
You are responsible for closing the provided client when appropriate.

Override the cache duration
---------------------------

Rarely, the client may want to override the default service discovery cache duration of five minutes.
To do so, pass a `~datetime.timedelta` as the ``cache_timeout`` argument to the `DiscoveryClient` constructor.

Most users of the client should not override the default cache timeout.
It was chosen to minimize network traffic but still allow Phalanx services to eventually converge on updated service discovery state.
If it is critical that a specific application immediately pick up new service discovery information, it should be restarted.

Next steps
==========

- Query for service URLs: :doc:`services`
- Query for datasets: :doc:`datasets`
- Query for Phalanx applications: :doc:`applications`
