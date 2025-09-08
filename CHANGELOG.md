# Change log

Repertoire is versioned with [semver](https://semver.org/).
Dependencies are updated to the latest available version during each release, and aren't noted here.

Repertoire is designed to be deployed via its [Phalanx](https://phalanx.lsst.io/) chart.
The interface between the service and its chart is internal and may change freely in minor and patch releases.
A change will only be considered backwards-incompatible if it results in backwards-incompatible changes for clients or requires changes to the Phalanx `values.yaml` files.

Find changes for the upcoming release in the project's [changelog.d directory](https://github.com/lsst-sqre/repertoire/tree/main/changelog.d/).

<!-- scriv-insert-here -->

<a id='changelog-0.1.0'></a>
## 0.1.0 (2025-09-08)

Initial release with support for a single data and service discovery endpoint and a client that can return Phalanx applications, datasets, and URLs for internal, data, and UI services.
