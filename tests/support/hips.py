"""Mock for a HiPS file server backend."""

import re

import respx
from httpx import Request, Response
from jinja2 import Template
from safir.testing.data import Data

from repertoire.dependencies.config import config_dependency

__all__ = ["MockHips", "register_mock_hips"]


class MockHips:
    """Pretend to be a HiPS file server but serve only the properties file."""

    def __init__(self, data: Data) -> None:
        template_path = data.path("input/properties.tmpl")
        self._template = Template(template_path.read_text())

    def get_properties(self, request: Request, *, path: str) -> Response:
        """Return a HiPS properties file.

        Parameters
        ----------
        request
            Incoming request.
        path
            Path of the dataset.

        Returns
        -------
        httpx.Repsonse
            Returns 200 with the templated properties file.
        """
        config = config_dependency.config()
        assert config.token
        token = config.token.get_secret_value()
        assert request.headers["Authorization"] == f"Bearer {token}"
        result = self._template.render(path=path)
        return Response(200, content=result.encode())


def register_mock_hips(
    data: Data, respx_mock: respx.Router, base_url: str
) -> None:
    """Mock out the HiPS server (properties file only).

    Parameters
    ----------
    data
        Test data holder.
    respx_mock
        Mock router.
    base_url
        Base URL of HiPS server.
    """
    mock = MockHips(data)
    base = re.escape(str(base_url).rstrip("/"))
    regex = rf"^{base}/(?P<path>.+)/properties$"
    respx_mock.get(url__regex=regex).mock(side_effect=mock.get_properties)
