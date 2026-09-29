:og:description: Learn how to configure datasets.

########
Datasets
########

In Repertoire, a dataset is a high-level collection of data with a corresponding set of services to access that data.
It roughly corresponds to an IVOA data collection.

Each deployment of Repertoire within a Phalanx environment needs to know what datasets are available in that environment.

.. note::

   In an unfortunate confusion of terminology, the `Butler <https://arxiv.org/abs/2206.14941>`__ uses "dataset" to refer to a single piece of data stored in the Butler, rather than a large collection of data such as a data release.
   The rough but still inaccurate Butler equivalent of a Repertoire dataset is a collection.
   For now, we are living with this ambiguity, since changing the Repertoire dataset terminology to something else would be a significant backwards-incompatible change.

Configuring known datasets
==========================

All datasets known to Repertoire are configured under ``config.datasets``.
Normally, they will all be listed in the main :file:`applications/repertoire/values.yaml` file, although it is possible for the per-environment configuration to add an additional dataset.

Each key under ``config.datasets`` is a dataset label.
This is the key that service discovery clients use to look up services for that dataset and will be widely advertised to users.

Below that key are the following keys describing the dataset:

``description`` (required)
    A human-readable description of the dataset.
    This should be about a paragraph and should describe what data is present and how it was obtained.

``docsUrl`` (optional)
    A URL pointing to additional documentation about the dataset.

``ivoaRegistry`` (optional)
    Additional metadata for the IVOA publishing registry.
    Publishing registry support is still being tested and is not yet documented.

Here is an example:

.. code-block:: yaml

   dp1:
     description: >-
       Data Preview 1 contains image and catalog products from the Example
       Science Pipelines v29 processing of observations obtained with the
       Commissioning Camera of seven ~1 square degree fields, over seven
       weeks in late 2024.
     docsUrl: "https://dp1.example.com/"
     ivoaRegistry:
       ivoid: "ivo://org.example/lsst-dp1/datasets"
       title: "Example DP1 Datasets"
       created: "2026-05-20T00:00:00"
       description: >-
         Dataset collection for Data Preview 1, serving as the resolvable
         registry target for per-object IVOIDs referencing Butler datasets
         and HiPS surveys from this data release.

Configuring available datasets
==============================

The presence of a key under ``config.datasets`` does not, by itself, cause Repertoire to provide discovery information for that dataset.
The dataset must also be listed in ``config.availableDatasets``.

The value of this configuration option must be a list of dataset labels that are available in a given Phalanx environment.
Normally, this option is only set in the per-environment :file:`applications/repertoire/values-{environment}.yaml` files in Phalanx.
For example:

.. code-block:: yaml
   :caption: values-idfprod.yaml

   config:
     availableDatasets:
       - "dp02"
       - "dp03"
       - "dp1"
       - "dp2"
       - "prompt"

ObsCore exporter configurations
===============================

Each dataset may have an associated ObsCore exporter configuration URL.
These configurations are used by services that need to generate IVOA ObsCore records from Butler results, such as SIA (see :dmtn:`300` and :sqr:`095`).

ObsCore exporter configurations are configured via ``config.obscoreConfigs``.
Each entry is a mapping from a dataset label to the URL of an ObsCore exporter configuration for that dataset.
This information is added to the service discovery results for each dataset along with the Butler configuration, if any (which is handled automatically by Phalanx).

An example:

.. code-block:: yaml

   config:
     obscoreConfigs:
       dp02: "https://example.com/obscore/configs/dp02.yaml"
       dp1: "https://example.com/obscore/configs/dp02.yaml"
       dp2: "https://example.com/obscore/configs/dp02.yaml"

Next steps
==========

- Services: :doc:`services`
- HiPS service: :doc:`hips`
- InfluxDB databases: :doc:`influxdb`
- TAP schema: :doc:`tap-schema`
