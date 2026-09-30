:og:description: Learn how to build service discovery data from Phalanx configuration.

.. py:currentmodule:: rubin.repertoire

#######################
Building discovery data
#######################

The normal way to access service discovery information is to request it from the local Repertoire server.
The server is responsible for reading the merged configuration from Phalanx and translating it into the service discovery REST API.

Some applications, however, require a static copy of service discovery information that can be used to look up documentation or URLs without running inside a Phalanx environment.
One example is `rsp.lsst.io <https://rsp.lsst.io/>`__, which is a static documentation site that should embed some URLs and documentation that are maintained as part of the Repertoire configuration.

To satisfy this use case, the rubin-repertoire PyPI package also provides the `RepertoireBuilder` class, which can construct a `Discovery` object from Repertoire configuration represented by a `RepertoireSettings` object.
The primary user of this API is the Phalanx documentation build process, which generates static discovery information for each known environment and makes that information available under `/discovery/environments <https://phalanx.lsst.io/discovery/environments/index.json>`__.

Using the builder
=================

Start by assembling a Repertoire configuration.
In the Phalanx case, this is done by merging the Repertoire :file:`values.yaml` file with the :file:`values-{environment}.yaml` file for an environment and then adding the additional configuration injected by Argo CD.
Unknown keys will be ignored, so the full Repertoire configuration can be used even though the builder and the `RepertoireSettings` model only recognize a subset of it.

Determine the base URL of the environment for which one is generating service discovery information.
Then, from that, determine the base URL of the Repertoire service itself, which is normally done by adding its ``config.pathPrefix`` setting.

Then, create a `RepertoireBuilder` object and call its `~RepertoireBuilder.build_discovery` method:

.. code-block:: python

   from rubin.repertoire import RepertoireBuilder, RepertoireSettings

   base_url = ...
   repertoire_base_url = ...
   settings = RepertoireSettings(...)
   builder = RepertoireBuilder(settings)
   discovery = builder.build_discovery(repertoire_base_url, base_url)

The result will be a fully-populated Pydantic model equivalent to what the Repertoire server returns from the ``/repertoire/discovery`` endpoint.
That model can then be serialized to JSON or used in whatever other way the calling application wants to use it.

The same approach can also be used to construct InfluxDB discovery information for a specific database using `RepertoireBuilder.build_influxdb`.
The result will be an `InfluxDatabase` model.

.. note::

   This support should only be used for the limited special cases where it is not possible to query a live discovery service.
   Currently, the Phalanx documentation build is the only known use case.
   This way of getting service discovery information is much less flexible and more fragile than asking the Repertoire server and should be avoided where possible.
