:og:description: Service discovery for Phalanx
:html_theme.sidebar_secondary.remove:

.. toctree::
   :hidden:

   User guide <user-guide/index>
   API <api>
   Change log <changelog>
   Contributing <dev/index>

##########
Repertoire
##########

Repertoire is a service and associated client library that provides service and data discovery for Phalanx_ environments, including the Rubin Science Platform.
The service is deployed in each Phalanx environment that requires service discovery.
The client is available from PyPI and intended for any service that needs to know the URLs of other Phalanx services or other information about what datasets and applications are deployed in the local Phalanx environment.

For more detailed information about the design of Repertoire, see :dmtn:`250`.

repertoire is developed on GitHub at https://github.com/lsst-sqre/repertoire.

.. grid:: 3

   .. grid-item-card:: User Guide
      :link: user-guide/index
      :link-type: doc

      Learn how to query Repertoire for data and service discovery information.

   .. grid-item-card:: API
      :link: api
      :link-type: doc

      See the full API documentation for the Repertoire client.

   .. grid-item-card:: Development
      :link: dev/index
      :link-type: doc

      Learn how to contribute to the Repertoire codebase.
