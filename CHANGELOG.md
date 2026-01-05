# Change log

Repertoire is versioned with [semver](https://semver.org/).
Dependencies are updated to the latest available version during each release, and aren't noted here.

Repertoire is designed to be deployed via its [Phalanx](https://phalanx.lsst.io/) chart.
The interface between the service and its chart is internal and may change freely in minor and patch releases.
A change will only be considered backwards-incompatible if it results in backwards-incompatible changes for clients or requires changes to the Phalanx `values.yaml` files.

Find changes for the upcoming release in the project's [changelog.d directory](https://github.com/lsst-sqre/repertoire/tree/main/changelog.d/).

<!-- scriv-insert-here -->

<a id='changelog-0.8.0'></a>
## 0.8.0 (2026-01-05)

### Backwards-incompatible changes

- TAP schema configuration now requires `databaseUrl` instead of individual `database` and `databaseUser` fields.

<a id='changelog-0.7.0'></a>
## 0.7.0 (2025-12-15)

### New features

- Add configuration for known TAP servers and their schema information. Currently, this is not used for discovery information, only for schema management.
- Add a new command-line tool to update a `TAP_SCHEMA` database using the new configuration information and [Felis](https://felis.lsst.io/).

<a id='changelog-0.6.1'></a>
## 0.6.1 (2025-12-04)

### Bug fixes

- Use updated Safir so that app metrics won't break the app in rare situations if the underlying Kafka infrastructure is down.

### Other changes

- Repertoire is now tested with Python 3.14 as well as 3.12 and 3.13.

<a id='changelog-0.6.0'></a>
## 0.6.0 (2025-10-17)

### Backwards-incompatible changes

- Move all data services in the discovery results model under datasets in a new per-dataset `services` key and eliminate the `data` key under the `services` top-level key.
- Move the HiPS list URL for a dataset into a new `hips` service under `services`, instead of a separate `hips_list` key directly under the dataset.

### New features

- Add new `list_influxdb_with_credentials` method to `RepertoireBuilderWithSecrets` to return all InfluxDB databases with credentials.
- Add new route `/discovery/influxdb` that returns connection information with credentials for every InfluxDB database known to Repertoire.
- Mark `description` and `docs_url` as optional for datasets in the service discovery model so that the same model can be used to parse the restricted output for Nublado. These fields remain mandatory in the Repertoire configuration, so in practice will always be present. This simplifies creation of mock data for service test suites.
- Allow the `services` key to be omitted in the service discovery model to simplify the creation of mock data for service test suites.
- Publish multi-platform images that support both linux/amd64 and linux/arm64.

<a id='changelog-0.5.0'></a>
## 0.5.0 (2025-10-03)

### Backwards-incompatible changes

- Add new mandatory `docsUrl` field for datasets in the Repertoire configuration, which is copied to the `docs_url` field in the per-dataset discovery information.

### New features

- Add new client method `build_nublado_dict`, which returns a stripped-down version of service discovery information in dictionary form suitable for JSON encoding. This will be used for service discovery inside [Nublado](https://nublado.lsst.io/) containers. The format is designed to maximize the chance it will continue working with old software stacks.
- Add client support for Python 3.12.

### Other changes

- Log a metrics event each time an authenticated user retrieves InfluxDB database credentials.

<a id='changelog-0.4.0'></a>
## 0.4.0 (2025-09-25)

### Backwards-incompatible changes

- Rename client methods `url_for_data_service`, `url_for_internal_service`, and `url_for_ui_service` to `url_for_data`, `url_for_internal`, and `url_for_ui`. These names are a bit more ambiguous, but less likely to make code lines obnoxiously long.
- Include InfluxDB connection information other than authentication credentials in the main discovery response rather than only a URL to the authenticated route. Put the URL to the authenticated route in a new `credentials_url` key.
- Add new client method `influxdb_connection_info` that returns only public connection information. Add new client method `influxdb_credentials` that requires a token argument and returns the full connection information including credentials.
- Remove client method `get_influxdb_connection_info` in favor of the new `influxdb_connection_info` client method.

### New features

- Add optional API versions to the configuration for data and internal services and include API versions in the discovery information. Each API version, if configured, is a mapping to an object containing the URL and the optional IVOA standardID.
- Add new client methods `versions_for_data` and `versions_for_internal` that list the available versions for data and internal services.
- Add an optional `version` argument to client methods `url_for_data` and `url_for_internal` to get the URL of a specific API version instead of the default URL.

### Bug fixes

- Accept and ignore a `sentry.enabled` key in the server configuration. This allows Phalanx configuration for Sentry to be added without failing on the unexpected configuration key.

<a id='changelog-0.3.0'></a>
## 0.3.0 (2025-09-23)

### Backwards-incompatible changes

- Add a `DiscoveryClient.aclose` method to cleanly shut down the internal HTTPX async client if one was not passed into the constructor. Users of the Repertoire client who do not use the FastAPI dependency and do not provide an HTTPX client to the `DiscoveryClient` constructor should call this method when they are done using the client.

### New features

- Add HiPS to the Repertoire configuration and use it to generate HiPS list URLs for every dataset with associated HiPS discovery information.
- Add support for generating a per-dataset HiPS list file on a separately-configurable route from the main Repertoire path prefix. The list file is assembled from HiPS properties files retrieved via HTTP, authenticated by a Gafaelfawr token.
- Add support for generating a separate HiPS list file for a single dataset on a legacy route.
- Add `rubin.repertoire.register_mock_discovery`. This function mocks service discovery results and is intended for use in test suites of applications that use the Repertoire client.
- Add a FastAPI dependency, `rubin.repertoire.discovery_dependency`, as the recommended way for FastAPI applications to manage a service discovery client.
- Support Slack and Sentry serialization with additional context in all of the exceptions raised by the Repertoire client.
- Add optional support for reporting exceptions to Sentry.

### Bug fixes

- Add upper major version bounds on the rubin-repertoire dependencies to ensure a human checks compatibility before allowing updates.

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
