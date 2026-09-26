:og:description: Learn how to configure discovery rules for the HiPS service.

####################################
HiPS service discovery configuration
####################################

Service discovery for HiPS (`Hierarchical Progressive Survey <https://www.ivoa.net/documents/HiPS/>`__) is not handled through :doc:`normal service discovery rules <services>`.
Repertoire is responsible for creating and serving the HiPS list files that list all available HiPS datasets, so it has to be configured with various HiPS-specific information in addition to the general service information.

If there are any HiPS trees configured for datasets that are enabled for the local Phalanx environment, Repertoire will synthesize HiPS data services and add them to the appropriate datasets.
The HiPS service therefore does not need, and should not have, its own data rule.
Instead, its service discovery properties are configured via the ``config.hips`` settings of Repertoire.

For more information about how HiPS is served by the Rubin Science Platform, see :dmtn:`230`.

Configuring available HiPS datasets
===================================

To configure the available HiPS datasets, set ``config.hips.datasets`` to a mapping from dataset names to the relative paths of HiPS trees relevant to that dataset.
For example:

.. code-block:: yaml

   hips:
     datasets:
       dp1:
         paths:
           - "deep_coadd/color_ugri"
           - "deep_coadd/color_gri"
           - "deep_coadd/color_izy"
           - "deep_coadd/color_riz"
           - "deep_coadd/color_ugr"
           - "deep_coadd/band_u"
           - "deep_coadd/band_g"
           - "deep_coadd/band_r"
           - "deep_coadd/band_i"
           - "deep_coadd/band_z"
           - "deep_coadd/band_y"
       dp2:
         paths:
           - "color_gri"
           - "color_u"
           - "color_g"
           - "color_r"
           - "color_i"
           - "color_z"
           - "color_y"

This says that the dataset ``dp1`` has 11 HiPS trees available, and the dataset ``dp2`` has 7 HiPS trees available.
As you can see, the paths are arbitrary and can contain multiple path segments.

Configuring HiPS URLs
=====================

There are two settings for the URLs under which HiPS files are served:

``config.hips.pathPrefix``
    The path prefix at which the HiPS ``list`` file will be served.
    A slash and the dataset label will be appended, followed by a slash and the literal word ``list``.

``config.hips.sourceTemplate``
    A Jinja_ template used to generate the base URL for a specific HiPS tree.
    It must be possible to append ``/properties`` to this URL to retrieve the corresponding HiPS ``properties`` file.
    This will also be used to construct the root URL to the HiPS tree to put into the ``list`` file.

So, for example, if the above dataset configuration is combined with:

.. code-block:: yaml

   hips:
     pathPrefix: "/api/hips/v2"
     sourceTemplate: "https://{{base_hostname}}/api/hips/v2/{{dataset}}"

then, for ``dp1``, Repertoire would expect a ``properties`` file under::

    https://{base_hostname}/api/hips/v2/dp1/deep_coadd/color_ugri

(and so on for the other paths), and would combine those ``properties`` files into a ``list`` file served at::

    https://{base_hostname}/api/hips/v2/dp1/list

Repertoire will use a Gafaelfawr token with the ``read:image`` scope to retrieve the ``properties`` files.

Configuring the legacy HiPS list route
--------------------------------------

Originally, the URLs to the HiPS list files did not have the dataset in the URL.
This meant only one HiPS list file was possible for a given instance of the Rubin Science Platform.

This mechanism was replaced with the above per-dataset paths, but Repertoire still supports serving that legacy HiPS list file for backwards compatibility.
To configure it, use the following settings:

``config.hips.legacy.dataset``
    The label of the dataset whose ``list`` file should be served at the legacy path.

``config.hips.legacy.pathPrefix``
    The route, relative to the base hostname of the environment, at which the ``list`` file will be served.
    The string ``/list`` will be added to that path prefix to form the URL for the legacy ``list`` file.

The individual HiPS tree URLs within that ``list`` file will still point to URLs constructed using ``config.hips.sourceTemplate`` as documented above.

Additional HiPS service metadata
================================

Similar to other data services, the following keys can be set under ``config.hips`` to add additional data to the HiPS service discovery entries.

``config.hips.title`` (optional)
    A short (aim for 40 characters or less) human-readable description of the HiPS service.

``config.hips.docsUrl`` (optional)
    A URL to more details about the HiPS service.

``config.hips.requiredScopes`` (optional)
    A list of the scopes required to access the HiPS service.
    A user must have all of the scopes listed.

``config.hips.quotaLabels`` (optional)
    A mapping of Gafaelfawr service names that may be used for quota restrictions to information about how that quota label is used.

See the more complete documentation of all of these keys in :doc:`services` for more details about their values.
