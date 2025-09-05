:og:description: Learn how to initialize the Repertoire client.

.. py:currentmodule:: rubin.repertoire

############################
Creating a Repertoire client
############################

Most users of Repertoire can create a client with a simple call to the constructor of `DiscoveryClient`:

.. code-block:: python

   from rubin.repertoire import DiscoveryClient


   discovery = DiscoveryClient()

However, some Phalanx configuration for the client is required first.

Phalanx configuration for Repertoire
====================================

The URL for the local Repertoire service will be obtained from the ``REPERTOIRE_BASE_URL`` environment variable.
This, in turn, should be injected into the client's environment via Phalanx, using the Phalanx ``global.repertoireUrl`` Helm variable, which is created by Argo CD.

If this environment variable is not set, the `DiscoveryClient` constructor will raise `RepertoireUrlError`.

Older applications whose Helm charts were created before Repertoire will not be configured to inject either this Helm setting or this environment variable.
See the Phalanx documentation on `adding Repertoire support <https://phalanx.lsst.io/developers/add-repertoire.html>`__ if you are adding Repertoire support to an older application.

Override the base URL
=====================

If the client knows the base URL for the Repertoire REST API via some other mechanism, it can override the base URL with a constructor paramter to `DiscoveryClient`:

.. code-block:: python

   from rubin.repertoire import DiscoveryClient


   discovery = DiscoveryClient(base_url="https://example.com/repertoire")

In this case, the environment variable is ignored and may be unset.

Provide an HTTPX client
=======================

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

Next steps
==========

- Query for service URLs: :doc:`services`
- Query for datasets: :doc:`datasets`
- Query for Phalanx applications: :doc:`applications`
