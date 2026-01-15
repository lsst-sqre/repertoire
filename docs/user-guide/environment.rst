:og:description: Getting the name of the local Phalanx environment.

.. py:currentmodule:: rubin.repertoire

############################
Getting the environment name
############################

To get a human-readable name for the local environment, call `DiscoveryClient.environment_name`:

.. code-block:: python

   from rubin.repertoire import DiscoveryClient


   discovery = DiscoveryClient()
   environment_name = await discovery.environment_name()

The result will be a human-readable name for the local Phalanx environment, or possibly `None` if no name is set.

The result may look like a hostname, since currently Phalanx environments are named that way.
However, the caller must not use this as a hostname, use it to form URLs, or otherwise treat it as anything other than a short human-readable name.

This method is only intended as a way to get a label for the environment for use in status and error reports or to identify the instance of a service to humans.

Next steps
==========

- Query for service URLs: :doc:`services`
- Query for datasets: :doc:`datasets`
