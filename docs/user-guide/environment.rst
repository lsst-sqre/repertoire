:og:description: Getting the name of the local Phalanx environment.

.. py:currentmodule:: rubin.repertoire

#########################################
Getting information about the environment
#########################################

To get information about the local Phalanx environment, call `DiscoveryClient.environment`.

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

Next steps
==========

- Query for service URLs: :doc:`services`
- Query for datasets: :doc:`datasets`
