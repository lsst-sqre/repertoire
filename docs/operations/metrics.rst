:og:description: Learn about the metrics exported by the Repertoire server.

#######
Metrics
#######

Repertoire optionally supports exporting events to Sasquatch_.
To enable this support, set ``config.metrics.enabled`` to true in the relevant :file:`values-{environment}.yaml` file and add ``repertoire`` to the list of metrics-enabled applications in the Sasquatch configuration.
See `the Sasquatch documentation <https://sasquatch.lsst.io/user-guide/app-metrics.html>`__ for more details.

By default, metrics are logged with an application name of ``repertoire`` and a topic prefix of ``lsst.square.metrics.events``.

If metrics reporting is enabled, the following events will be logged.

influxdb_creentials
    An authenticated user retrieved the credentials for an InfluxDB database.
    The username will be in the ``username`` tag.
    The label for the InfluxDB database will be in the ``label`` field.
