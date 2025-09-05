:og:description: Listing applications installed in the local environment.

.. py:currentmodule:: rubin.repertoire

####################
Listing applications
####################

To get a list of all Phalanx applications enabled in the local environment, call `DiscoveryClient.applications`:

.. code-block:: python

   from rubin.repertoire import DiscoveryClient


   discovery = DiscoveryClient()
   applications = await discovery.applications()

The result is a list of Phalanx application names.
These are the same names used in the `Phalanx applications list <https://phalanx.lsst.io/applications/index.html>`__, without the description or category.

Phalanx applications are not the same as service names.
Many Phalanx applications do not register a service for service discovery, some register multiple services, and in some cases the service name is different from the application name.

This method is relatively rarely used.
It is primarily intended for services such as `mobu <https://mobu.lsst.io/>`__ that make decisions based on the Phalanx applications deployed in the environment.

Next steps
==========

- Query for service URLs: :doc:`services`
- Query for datasets: :doc:`datasets`
