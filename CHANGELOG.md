# Change log

Repertoire is versioned with [semver](https://semver.org/).
Dependencies are updated to the latest available version during each release, and aren't noted here.

Repertoire is designed to be deployed via its [Phalanx](https://phalanx.lsst.io/) chart.
The interface between the service and its chart is internal and may change freely in minor and patch releases.
A change will only be considered backwards-incompatible if it results in backwards-incompatible changes for clients or requires changes to the Phalanx `values.yaml` files.

Find changes for the upcoming release in the project's [changelog.d directory](https://github.com/lsst-sqre/repertoire/tree/main/changelog.d/).

<!-- scriv-insert-here -->

<a id='changelog-0.2.0'></a>
## 0.2.0 (2025-09-10)

### Backwards-incompatible changes

- Change the input configuration for datasets to be a mapping of dataset label to metadata instead of a list, and add a mandatory `description` field for datasets.
- Change the model for discovery information to return datasets as a mapping of label to metadata instead of a list of mappings with `name` keys.
- Add new `availableDatasets` configuration parameter to list the datasets available in a given environment, allowing that list to be separated from shared metadata about all available datasets.
- Rename the `urls` field of discovery information to `services`.
- Convert the values of the `data`, `internal`, and `ui` mappings to be full objects, moving the URL into the `url` field of that object. This creates room for additional fields in the future.
- Rename `RepertoireBuilder.build` to `RepertoireBuilder.build_discovery` now that there are multiple types of information that the builder can build.

### New features

- Add `RepertoireBuilder.build_influxdb` to construct InfluxDB discovery information, and a new class, `RepertoireBuilderWithSecrets`, with method `build_influxdb_with_credentials`, to build InfluxDB discovery information including credentials.
- Add a new route, `/discovery/influxdb/{database}`, that returns InfluxDB discovery information with credentials. This route will be protected by Gafaelfawr authentication.
- Add corresponding models and client methods `influxdb_databases` and `get_influxdb_connection_info` to retrieve the new information.
- Add the `description` field to the model for datasets.
- Add an optional `openapi` key to service information for data and internal services, which contains a URL for the OpenAPI JSON schema if set. Add support for that field to the corresponding service generation rules.

<a id='changelog-0.1.0'></a>
## 0.1.0 (2025-09-08)

Initial release with support for a single data and service discovery endpoint and a client that can return Phalanx applications, datasets, and URLs for internal, data, and UI services.
