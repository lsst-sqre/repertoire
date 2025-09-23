:og:description: Testing programs that use the Repertoire client.

.. py:currentmodule:: rubin.repertoire

######################################
Testing users of the Repertoire client
######################################

When testing software that uses the Repertoire client for service discovery, the test suite needs to be able to inject test service discovery information and prevent attempts to contact a real service discovery service.
`rubin.repertoire` provides a function, `register_mock_discovery`, to simplify this test setup.

Prerequisites
=============

Since the Repertoire client uses HTTPX_, `register_mock_discovery` relies on respx_ to mock the service discovery URL.
The package being tested must therefore depend on respx_ in whatever dependency group it uses for tests that need service discovery mocking.

The Repertoire client does not itself depend on respx_ and expects the mock router to be passed into `register_mock_discovery`.

Mocking service discovery results
=================================

First, create the mocked service discovery results that you want the test to use.
It's often sufficient to create one set of mocked results that can be used by the entire test suite.

`register_mock_discovery` accepts these results in any of three formats:

- A `Discovery` object.
- A Python `dict` holding the serialized form of a `Discovery` object (the same as the JSON output produced by the Repertoire server's ``/discovery`` route).
- A `~pathlib.Path` for a file containing the serialized form of a `Discovery` object in JSON format.

Then, call `register_mock_discovery`, passing in the ``respx_mock`` fixture object and the mocked discovery results.
Normally, this is best done in a fixture defined in :file:`tests/conftest.py`.
For example:

.. code-block:: python

   import pytest
   import respx
   from pathlib import Path
   from rubin.repertoire import register_mock_discovery


   @pytest.fixture(autouse=True)
   def mock_discovery(
       respx_mock: respx.Router, monkeypatch: pytest.MonkeyPatch
   ) -> Discovery:
       monkeypatch.setenv("REPERTOIRE_BASE_URL", "https://example.com/repertoire")
       path = Path(__file__).parent / "data" / "discovery.json"
       return register_mock_discovery(respx_mock, path)

This fixture assumes :file:`tests/data/discovery.json` contains the mock service discovery results in JSON format.
It is set up as an autouse fixture that will affect all tests.
If you need to vary service discovery results by test, you will need to do something more complex, such as multiple fixtures.

Note that this fixture uses pytest's ``monkeypatch.setenv`` to set ``REPERTOIRE_BASE_URL`` to a base URL for the mocked Repertoire service.
This is the recommended pattern, since this environment variable will also be used by the Repertoire client and ensures the client queries the mocked URL.

However, you can instead pass the base URL to `register_mock_discovery` as its third argument if you choose, in which case the environment variable will be ignored and does not need to be set.

This fixture returns the `Discovery` model.
This allows tests to explicitly depend on the fixture and reference that model for expected URLs that show up in test results
This can avoid accidental mismatches test URLs between the mock service discovery results and the tests.
