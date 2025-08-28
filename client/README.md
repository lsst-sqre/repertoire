# rubin-repertoire

rubin-repertoire is a client for [Repertoire](https://repertoire.lsst.io/), which provides service discovery for [Phalanx](https://phalanx.lsst.io/).
This package provides the Python client, Pydantic models, and logic for generating service discovery information from Phalanx configuration files.
The latter is used by the Phalanx documentation build.

This package is intended for use inside Phalanx services.
User notebooks running under [Nublado](https://nublado.lsst.io/) should instead use the client included in `lsst.rsp`, which supports a wider range of Python versions.

rubin-repertoire is available from [PyPI](https://pypi.org/project/rubin-repertoire/):

```sh
pip install rubin-repertoire
```

For full documentation, see [the Repertoire user guide](https://repertoire.lsst.io/user-guide/).
