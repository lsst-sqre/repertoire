:og:description: Learn how to configure and administer the Repertoire server.

################
Operations guide
################

The Repertoire server is a `Phalanx application <https://phalanx.lsst.io/applications/repertoire/index.html>`__.
It is considered part of Phalanx infrastructure and is normally installed in every Phalanx environment.

Repertoire configuration is done via its Helm chart in Phalanx_

.. toctree::
   :caption: Configuration
   :maxdepth: 1

   services
   hips
   datasets
   influxdb
   tap-schema

.. toctree::
   :caption: Server operations
   :maxdepth: 1

   metrics
