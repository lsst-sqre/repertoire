"""Mock for a HiPS file server backend."""

from __future__ import annotations

import re

import respx
from httpx import Request, Response
from jinja2 import Template

from repertoire.dependencies.config import config_dependency

from .data import data_path

__all__ = ["MockHips", "register_mock_hips"]


class MockHips:
    """Pretend to be a HiPS file server but serve only the properties file."""

    def __init__(self) -> None:
        template_path = data_path("input/properties.tmpl")
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


def register_mock_hips(respx_mock: respx.Router, base_url: str) -> None:
    """Mock out the HiPS server (properties file only).

    Parameters
    ----------
    respx_mock
        Mock router.
    base_url
        Base URL of HiPS server.
    """
    mock = MockHips()
    base = re.escape(str(base_url).rstrip("/"))
    regex = rf"^{base}/(?P<path>.+)/properties$"
    respx_mock.get(url__regex=regex).mock(side_effect=mock.get_properties)
