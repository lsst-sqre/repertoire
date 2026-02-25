:og:description: Managing TAP_SCHEMA metadata with Repertoire.

##################################
TAP_SCHEMA metadata management
##################################

Repertoire manages TAP_SCHEMA metadata for TAP applications that use CloudSQL or external PostgreSQL databases.
When TAP_SCHEMA management is enabled for a TAP service, Repertoire will automatically populate and update the schema metadata
during deployment upgrades.

For TAP applications using containerized (in-cluster) databases, see :ref:`tap-schema-containerized`.

.. _tap-schema-overview:

Overview
========

TAP_SCHEMA is a set of database tables that describe the schemas, tables, and columns available through a TAP service.
Clients use this metadata to discover what data is queryable, either via ADQL queries or using the VOSI ``/tables`` endpoint.

Repertoire populates TAP_SCHEMA by:

#. Downloading schema definitions from `sdm_schemas <https://github.com/lsst/sdm_schemas>`__ (or another configurable source).
#. Parsing the YAML schema files using `Felis <https://felis.lsst.io/>`__.
#. Loading the schema metadata into a staging PostgreSQL schema.
#. Validating the staged data.
#. Performing an atomic swap to make the new metadata live.

This process runs automatically as a Helm **pre-install/pre-upgrade hook** during Argo CD syncs of Repertoire.

If the CloudSQL proxy is needed (``cloudsql.enabled`` in Repertoire's Phalanx values), it runs as an init container in the job pod to provide connectivity.

.. _tap-schema-configuration:

Configuration
=============

TAP_SCHEMA management is configured in the Repertoire application's Helm values in Phalanx (``applications/repertoire/values.yaml`` and environment-specific overrides).

Global settings
---------------

This configuration applies to all TAP servers unless overridden per-server.

``config.tap.schemaVersion``
   The sdm_schemas version to use.
   This is a tag from the `sdm_schemas repository <https://github.com/lsst/sdm_schemas>`__.

``config.tap.schemaSourceTemplate``
   URL template for downloading the sdm_schemas archive.
   Uses ``{version}`` as a placeholder.
   Default: ``"https://github.com/lsst/sdm_schemas/archive/refs/tags/{version}.tar.gz"``

   Supported URL schemes: ``https://``, ``http://``, ``gs://`` (Google Cloud Storage).

Per-server settings
-------------------

Each TAP server is configured under ``config.tap.servers.<name>``, where ``<name>`` matches the Phalanx application name (e.g., ``tap``, ``ssotap``, ``livetap``).

``config.tap.servers.<name>.enabled``
   Whether Repertoire should manage updating the TAP_SCHEMA for this server.
   Set to ``false`` in environments where the TAP server doesn't exist or uses containerized databases.
   Default: ``false``.

``config.tap.servers.<name>.schemas``
   List of schema names to load.
   These correspond to YAML file names (without the ``.yaml`` extension) in the sdm_schemas package.
   Note that the order of this list determines the display order in TAP clients via the ``tap_schema_index`` parameter passed to Felis.

   Example:

   .. code-block:: yaml

      schemas:
        - dp1
        - ivoa_obscore
        - dp02_dc2

   In this example, ``dp1`` will appear first (index 1), ``ivoa_obscore`` second (index 2), and ``dp02_dc2`` third (index 3).

``config.tap.servers.<name>.schemaVersion``
   Override the global ``schemaVersion`` for this specific server.
   If not set, the global ``config.tap.schemaVersion`` is used.

``config.tap.servers.<name>.databaseUrl``
   PostgreSQL connection URL for the TAP_SCHEMA database.
   Format: ``postgresql://user@host:port/database``

   When using the CloudSQL backend this would typically be ``127.0.0.1:5432`` since the Cloud SQL proxy provides a local endpoint.

``config.tap.servers.<name>.databasePasswordKey``
   Key name in the Repertoire Vault secret that contains the database password.
   The password is provided to the job via the ``REPERTOIRE_DATABASE_PASSWORD`` environment variable.

Full example
------------

.. code-block:: yaml

   # In applications/repertoire/values.yaml (defaults)
   config:
     tap:
       schemaVersion: "w.2026.01"
       schemaSourceTemplate: "https://github.com/lsst/sdm_schemas/archive/refs/tags/{version}.tar.gz"
       servers:
         tap:
           enabled: false
           schemas:
             - dp1
             - ivoa_obscore
             - dp02_dc2
           databaseUrl: "postgresql://tap@127.0.0.1:5432/tap"
           databasePasswordKey: "tap-database-password"
         ssotap:
           enabled: false
           schemas:
             - dp03_10yr
             - dp03_1yr
           databaseUrl: "postgresql://ssotap@127.0.0.1:5432/ssotap"
           databasePasswordKey: "ssotap-database-password"

   # In applications/repertoire/values-idfint.yaml (environment override)
   config:
     tap:
       servers:
         tap:
           enabled: true
         ssotap:
           enabled: true

   cloudsql:
     enabled: true
     instanceConnectionName: "project:region:instance"
     serviceAccount: "repertoire@project.iam.gserviceaccount.com"

.. _tap-schema-common-tasks:

Common tasks
============

Updating the sdm_schemas version
---------------------------------

To update the schema definitions to a new sdm_schemas release:

#. Change ``config.tap.schemaVersion`` in ``applications/repertoire/values.yaml`` to the new version tag for sdm_schemas.

#. If the ``cadc-tap`` chart's ``config.datalinkPayloadUrl`` references a specific sdm_schemas version, update that as well in ``charts/cadc-tap/values.yaml``.

#. Commit and push the changes, then sync the Repertoire application via ArgoCD. A helm hook will run for each enabled TAP service, and will automatically download the new schema version and update TAP_SCHEMA.

Adding or removing schemas from a TAP server
---------------------------------------------

To change which schemas are served by a TAP application:

#. Edit the ``schemas`` list under ``config.tap.servers.<name>`` in ``applications/repertoire/values.yaml``.

#. Add or remove schemas. Added schema names must match YAML file names in the sdm_schemas package (without the ``.yaml`` extension).

#. Sync the Repertoire application. The Helm hook will reload all schemas for that server.

Changing schema display order
-----------------------------

The order of schemas in the ``schemas`` list directly controls the ``tap_schema_index`` used by TAP clients such as Firefly to order schemas in their UI.

.. code-block:: yaml

   # dp1 will appear first, then dp02_dc2, then ivoa_obscore
   schemas:
     - dp1
     - dp02_dc2
     - ivoa_obscore

Adding a new TAP server to Repertoire management
-------------------------------------------------

To have Repertoire manage TAP_SCHEMA for a new TAP application:

#. Add a new entry under ``config.tap.servers`` in ``applications/repertoire/values.yaml``:

   .. code-block:: yaml

      config:
        tap:
          servers:
            newtap:
              enabled: false
              schemas:
                - my_schema
              databaseUrl: "postgresql://newtap@127.0.0.1:5432/newtap"
              databasePasswordKey: "newtap-database-password"

#. Add the corresponding secret to ``applications/repertoire/secrets.yaml``:

   .. code-block:: yaml

      newtap-database-password:
        description: >-
          Database password for the newtap service, used by repertoire to manage
          the newtap TAP_SCHEMA.
        if: config.tap.servers.newtap.enabled
        copy:
          application: newtap
          key: tap-schema-password

#. Enable the server in the appropriate environment values file (e.g., ``applications/repertoire/values-idfint.yaml``):

   .. code-block:: yaml

      config:
        tap:
          servers:
            newtap:
              enabled: true

#. Ensure the TAP application itself has ``tap-schema-password`` in its Vault secrets and that the TAP_SCHEMA database type is set to ``"cloudsql"`` or ``"external"`` (not ``"containerized"``).

.. _tap-schema-secrets:

Secrets
=======

Repertoire requires database credentials to connect to each TAP server's TAP_SCHEMA database.
Database passwords are **copied** from the corresponding TAP application's Vault secrets using the ``copy`` directive in ``applications/repertoire/secrets.yaml``.

This means you only need to manage the password in one place (the TAP application's Vault path), and Repertoire will automatically have access to it.

The password key name for each server is configured via ``databasePasswordKey`` in the server configuration.
This is injected into the schema update job via the ``REPERTOIRE_DATABASE_PASSWORD`` environment variable.

.. _tap-schema-containerized:

Containerized databases
=======================

When a TAP application uses the **containerized** (in-cluster) database backend, Repertoire does **not** manage its TAP_SCHEMA metadata.
For this setup the schema metadata is embedded directly in the MySQL Docker image that runs as the TAP_SCHEMA database pod.

These images are configured in the TAP application's Helm values:

.. code-block:: yaml

   cadc-tap:
     tapSchema:
       type: "containerized"
       image:
         repository: "lsstsqre/tap-schema-usdf-prod-tap"
         tag: "w.2026.01"

To update TAP_SCHEMA metadata for a containerized deployment:

#. Build a new Docker image containing the updated schema metadata.
#. Push the image to the container registry.
#. Update ``tapSchema.image.tag`` in the environment-specific TAP values file.
#. Sync the TAP application via Argo CD.

For information on setting up TAP database infrastructure, see the `Phalanx TAP database configuration guide <https://phalanx.lsst.io/applications/tap/databases.html>`__.
