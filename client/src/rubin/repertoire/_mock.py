"""Mock for the Repertoire discovery service."""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from httpx import Response

from ._exceptions import RepertoireUrlError
from ._models import Discovery

# Avoid an explicit dependency on respx, which the caller will, of necessity,
# depend on before using this interface, and which is not otherwise required
# by the client.
if TYPE_CHECKING:
    import respx

__all__ = ["register_mock_discovery"]


def register_mock_discovery(
    respx_mock: "respx.Router",
    results: Discovery | dict[str, Any] | Path,
    base_url: str | None = None,
) -> Discovery:
    """Mock out the Repertoire discovery server.

    This does not mock retrieval of InfluxDB connection information.

    Parameters
    ----------
    respx_mock
        Mock router.
    results
        Mock results to return when HTTPX code requests service discovery.
        This can be a `~rubin.repertoire.Discovery` object, the equivalent as
        a `dict` (using the same syntax as parsed JSON), or a `~pathlib.Path`
        to a JSON file.
    base_url
        Base URL at which to mock the Repertoire service. If this is not
        given, the environment variable ``REPERTOIRE_BASE_URL`` must be set
        before calling this function (usually via pytest's
        ``monkeypatch.setenv``) and will be used as the default.

    Returns
    -------
    Discovery
        Parsed discovery results that will be returned from the mocked
        endpoint.

    Raises
    ------
    RepertoireUrlError
        Raised if ``REPERTOIRE_BASE_URL`` is not set in the environment and
        ``base_url`` is not provided.
    """
    if isinstance(results, Discovery):
        discovery = results
    elif isinstance(results, Path):
        discovery = Discovery.model_validate_json(results.read_text())
    else:
        discovery = Discovery.model_validate(results)
    discovery_json = discovery.model_dump(mode="json", exclude_defaults=True)
    if not base_url:
        base_url = os.getenv("REPERTOIRE_BASE_URL")
        if not base_url:
            raise RepertoireUrlError
    url = base_url.rstrip("/") + "/discovery"
    respx_mock.get(url).mock(return_value=Response(200, json=discovery_json))
    return discovery
