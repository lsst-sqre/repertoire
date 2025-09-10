:og:description: Getting InfluxDB connection information.

.. py:currentmodule:: rubin.repertoire

#######################################
Getting InfluxDB connection information
#######################################

Repertoire supports obtaining connection information for InfluxDB databases.
Unlike other service discovery calls, the connection information includes credentials and therefore this API requires authentication.
Also unlike other service discovery calls, the InfluxDB database may not be in the same Phalanx environment.

Listing available databases
===========================

To get a list of InfluxDB databases for which connection information is available, call `DiscoveryClient.influxdb_databases`:

.. code-block:: python

   from rubin.repertoire import DiscoveryClient


   discovery = DiscoveryClient()
   databases = await discovery.influxdb_databases()

The resulting names are short, human-readable names that can be passed as the ``database`` parameter to `DiscoveryClient.get_influxdb_connection_info` as described below.

Getting connection information
==============================

Getting the connection information for a specific database requires authentication, since the returned information includes the username and password.

First, obtain a Gafaelfawr_ token.
Inside a service, normally this should be a delegated token received as part of a request and used to act on behalf of the user.
See the `Gafaelfawr documentation on delegated tokens <https://gafaelfawr.lsst.io/user-guide/gafaelfawringress.html#requesting-delegated-tokens>`__ for more information.
In other environments, this may be a user token created through the token UI, or a notebook token created by Nublado_.

Then, call `DiscoveryClient.get_influxdb_connection_info` with the name of the database (possibly obtained via `DiscoveryClient.influxdb_databases`) and that token:

.. code-block:: python

   from rubin.repertoire import DiscoveryClient


   discovery = DiscoveryClient()
   token = "..."  # obtained from somewhere else
   info = await discovery.get_influxdb_connection_info("some_database", token)

The resulting object has the following fields:

``url``
    The URL of the InfluxDB service for this database.
    This is a ``pydantic.HttpUrl`` without authentication information.
    Use the ``host``, ``port``, and ``path`` attributes of the URL if you need those components separately (for the constructor of `aioinflux.client.InfluxDBClient`, for example).

``database``
    The name of the InfluxDB database to use for queries.

``username``
    Username with which to authenticate.

``password``
    Password with which to authenticate.

``schema_registry``
    The URL (as a string) of the associated `Confluent Kafka Schema Registry <https://docs.confluent.io/platform/current/schema-registry/index.html>`__ that contains schema information for this database.
