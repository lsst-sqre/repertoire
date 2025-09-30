:og:description: Learn how to generate stripped-down discovery information for Nublado.

.. py:currentmodule:: rubin.repertoire

#####################################
Discovery data for Nublado containers
#####################################

Nublado_ is the JupyterLab component of Phalanx.
It allows scientists to work inside a container with a possibly older and frozen version of a scientific toolchain so that scientific results are more easily reproducible.

.. _Nublado: https://nublado.lsst.io/

Nubaldo containers may not be able to run the latest versions of client software, but still need service and dataset discovery.
This need is met by providing, inside the container, a pre-generated JSON file containing current service discovery information.
The format provides only the information likely to be needed by scientific payloads and omits most of the information in normal service discovery results to minimize the need for backward-incompatible changes.

Generation of this file will be done by the Nublado_ controller.
The lsst.rsp_ library is responsible for reading this file and answering discovery questions from it.

.. _lsst.rsp: https://github.com/lsst-sqre/lsst-rsp

Data format
===========

Discovery information is written in JSON format to a file inside the container named :file:`/etc/nublado/discovery/v1.json`.
The format parallels the current `Discovery` object with the following changes:

#. The ``applications`` key is not present.
#. Only ``butler_config`` is included as data for each dataset in ``datasets``.
   Datasets without a Butler configuration will have an empty object value.
#. Internal and UI services are omitted.
#. All data for data services is omitted except for ``url`` at the top level and under any ``versions`` dictionary.

Any client reading this data should silently ignore any new fields.

In the future, if some new feature forces a backwards-incompatible revision of this format, Repertoire will retain the ability to generate the v1 version of the data and the new format will use a :file:`v2.json` path.
This will allow older software to continue to use the v1 JSON file with the features that it supported.

Generating the data
===================

To generate the data for this JSON file, call `DiscoveryClient.build_nublado_dict`.

The result of this method will be a Python dictionary whose contents have been converted to simple Python data types (`str`, `dict`, etc.).
This data structure is suitable for JSON serialization.

For example:

.. code-block:: python

   import json
   from rubin.repertoire import DiscoveryClient

   discovery = DiscoveryClient()
   nublado_dict = await discovery.build_nublado_dict()
   nublado_json = json.dumps(nublado_dict, sort_keys=True, indent=2)
