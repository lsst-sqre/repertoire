:og:description: Getting information about the local Phalanx environment.

.. py:currentmodule:: rubin.repertoire

#################################################
Getting information about the Phalanx environment
#################################################

Most Repertoire clients should ask directly for the :doc:`services <services>`, :doc:`datasets <datasets>`, or :doc:`InfluxDB databases <influxdb>` that they want to use.
If the response is `None`, that service or dataset is not available, and the client can do something appropriate.

However, sometimes a client wants to know more general information about the local environment.
For example, `mobu <https://mobu.lsst.io>`__ uses the name of the environemnt in status reporting and needs the list of Phalanx applications to decide what notebooks to run.
Those special-case applications can use the following APIs.

Do not use these APIs for service discovery.
Their use should be rare; most clients should use other APIs.

General information about the environment
=========================================

To get general information about the local Phalanx environment, call `DiscoveryClient.environment`.

.. code-block:: python

   from rubin.repertoire import DiscoveryClient

   discovery = DiscoveryClient()
   environment = await discovery.environment()
   print("Environment", environment.name)

The result will be an object with various information about the local Phalanx environment, or possibly `None` if no information is configured.
If not `None`, the object will have the following keys:

``name``
    A human-readable name for the environment.
    The result may look like a hostname, since currently Phalanx environments are named that way.
    However, the caller must not use this as a hostname, use it to form URLs, or otherwise treat it as anything other than a short human-readable name.

``title``
    A short human-readable title for the environment.

``title_long``
    A longer (but still brief) title for the environment.

``label``
    The Phalanx label for the environment.
    This is the same as the name used for the environment inside the Phalanx repository.
    Prefer ``name`` or ``title`` in information presented to users (as opposed to environment administrators), since the label may not be meaningful to a user.

``description``
    An extended description of the environment.
    This will generally be a paragraph with one or more sentences.

``docs_url``
    URL to more documentation about this Phalanx environment.

.. note::

   Earlier versions of the Repertoire client only provided `DiscoveryClient.environment_name`.
   This method is still available, but it is deprecated and will be removed in a future release of Repertoire.
   Prefer `DiscoveryClient.environment` and then use the ``name`` attribute of the resulting object.

Listing applications
====================

To get a list of all Phalanx applications enabled in the local environment, call `DiscoveryClient.applications`:

.. code-block:: python

   from rubin.repertoire import DiscoveryClient

   discovery = DiscoveryClient()
   applications = await discovery.applications()

The result is a list of Phalanx application names.
These are the same names used in the `Phalanx applications list <https://phalanx.lsst.io/applications/index.html>`__, without the description or category.

Phalanx applications are not the same as service names.
Many Phalanx applications do not register a service for service discovery, some register multiple services, and in some cases the service name is different from the application name.
Only applications that know exactly what this data is for and need to use Phalanx application names specifically should use this method.

Next steps
==========

- Query for service URLs: :doc:`services`
- Query for datasets: :doc:`datasets`
- Query for InfluxDB databases: :doc:`influxdb`
- Testing: :doc:`testing`
