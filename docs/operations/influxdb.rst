:og:description: Learn how to configure InfluxDB databases.

##################
InfluxDB databases
##################

Repertoire can provide service discovery of InfluxDB databases and an associated Confluent Schema Registry, both provided by Sasquatch_.
In addition to providing general discovery information, Repertoire can also provide authentication credentials to authenticated clients.

Configuring known InfluxDB databases
====================================

InfluxDB databases are configured via the ``config.influxdbDatabases`` Helm chart setting.
Unlike most other Repertoire configuration, this key should only be set in environment-specific :file:`applications/repertoire/values-{environment}.yaml`.
The available InfluxDB databases is different in each environment; there are no databases available in all environments, and only a few that are accessible from more than one environment.

Each key under ``config.influxdbDatabases`` is an InfluxDB database label, which will be used by clients to find connection information and authentication credentials for that database.
By convention, these labels begin with the Phalanx environment name followed by an underscore.
This aids in distinguishing databases since some databases are accessible from remote Phalanx environments.

Below that top-level label, the following keys are supported:

``url`` (required)
    The URL to the InfluxDB database API.

``database`` (required)
    The name of the database inside InfluxDB.
    This is usually different from the label due to the above-mentioned label convention.

``schemaRegistry`` (required)
    The URL to the Confluent Schema Registry for this InfluxDB database.
    This may be an internal URL that is usable only within the same Kubernetes environment as the Repertoire server.

``local`` (optional)
    If set to true (the default is false), indicates that the database is local to this Phalanx environment.
    This can be used by service discovery clients to find only the local InfluxDB databases and exclude databases hosted by other Phalanx environments that are merely accessible from this one.

``username`` (required)
    Username to use for authentication to this InfluxDB database when using retrieved credentials.

``passwordKey`` (required)
    Key in the Repertoire Vault secret that holds the password to use for authentication to this InfluxDB database.
    This password and the value of ``username`` are returned to authenticated clients that request access to this database.

The information from the last two fields is only returned to clients that have authenticated with the ``read:sasquatch`` scope and are requesting InfluxDB credentials.
See :ref:`influxdb-credentials` for more information.

Here is an example:

.. code-block:: yaml

   config:
     influxdbDatabases:
       idfdev_efd:
         url: "https://data-dev.example.com/influxdb/"
         database: "efd"
         username: "efdreader"
         passwordKey: "idfdev_efd-password"
         schemaRegistry: "http://sasquatch-schema-registry.sasquatch:8081"
         local: true

Configuring InfluxDB credentials
================================

Every registered InfluxDB database must have a corresponding password that is returned by Repertoire to authenticated clients requesting InfluxDB credentials.
This is handled through the `Phalanx secrets mechanism <https://phalanx.lsst.io/admin/secrets-setup.html>`__.

When adding a new InfluxDB database, for any environment, add an entry to the corresponding :file:`applications/repertoire/secrets-{environment}.yaml` file for that environment defining a new secret to hold the password.
Here is an example entry corresponding to the above example configuration:

.. code-block:: yaml

   idfdev_efd-password:
     description: >-
       InfluxDB password for the efdreader user for accessing the EFD
       database on idfdev. Clients will cache this secret locally in their
       client configuration, so changing it may be disruptive.

Then, populate that secret using the normal Phalanx mechanisms for the environment.
Ensure the name of the secret matches the ``passwordKey`` field of the corresponding ``config.influxdbDatabases`` entry.
