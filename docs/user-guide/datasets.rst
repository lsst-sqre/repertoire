:og:description: Listing datasets available in the local environment.

.. py:currentmodule:: rubin.repertoire

################
Listing datasets
################

To list all of the datasets available in the local environment, call `DiscoveryClient.datasets`.
The result will be a list of the short dataset names.

These names are the valid arguments for the dataset parameters to `DiscoveryClient.url_for_data_service` and `DiscoveryClient.butler_config_for` in that environment.

For example:

.. code-block:: python

   from rubin.repertoire import DiscoveryClient


   discovery = DiscoveryClient()
   datasets = await discovery.datasets()
   for dataset in datasets:
       url = await discovery.url_for_data_service("cutout", dataset)
       if url:
           print(f"Cutout API for {dataset}: {url}")
       else:
           print(f"Cutouts for {dataset} not available")

Currently, only the names of datasets are returned.
More information about datasets will likely be available in future versions.

Next steps
==========

- Query for service URLs: :doc:`services`
- Query for Phalanx applications: :doc:`applications`
