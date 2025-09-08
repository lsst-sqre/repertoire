"""Models for Repertoire service discovery."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl

__all__ = [
    "Dataset",
    "Discovery",
    "ServiceUrls",
]


class Dataset(BaseModel):
    """Discovery information about a single dataset."""

    name: Annotated[
        str,
        Field(
            title="Name",
            description="Human-readable name of the dataset",
            examples=["dp02", "dp1"],
        ),
    ]

    butler_config: Annotated[
        HttpUrl | None,
        Field(
            title="Butler config URL",
            description=(
                "URL of Butler configuration to access this dataset, if it is"
                " available via a Butler server"
            ),
            examples=[
                "https://example.cloud/api/butler/repo/dp02/butler.yaml"
            ],
        ),
    ] = None


class ServiceUrls(BaseModel):
    """Mappings of service names to base URLs."""

    data: Annotated[
        dict[str, dict[str, HttpUrl]],
        Field(
            title="Service to dataset to URL",
            description=(
                "Mapping of service names to dataset names served by that"
                " service to base URLs. The dataset name will match the name"
                " of one of the datasets in the associated discovery reply."
                " These are the API services used directly by users for data"
                " access."
            ),
            examples=[
                {
                    "hips": {
                        "dp02": "https://data-dev.lsst.cloud/api/hips/v2/dp02",
                        "dp1": "https://data-dev.lsst.cloud/api/hips/v2/dp1",
                    },
                }
            ],
        ),
    ] = {}

    internal: Annotated[
        dict[str, HttpUrl],
        Field(
            title="Internal service URLs",
            description=(
                "Mapping of service name to base URL for internal services."
                " These are used by other services and generally won't be"
                " used directly by services."
            ),
            examples=[
                {
                    "gafaelfawr": "https://data-dev.lsst.cloud/auth/api/v1",
                    "wobbly": "https://data-dev.lsst.cloud/wobbly",
                }
            ],
        ),
    ] = {}

    ui: Annotated[
        dict[str, HttpUrl],
        Field(
            title="User interface URLs",
            description=(
                "Mapping of service name to base URL for user interfaces"
                " intended for access by a user using a web browser."
            ),
            examples=[
                {
                    "argocd": "https://data-dev.lsst.cloud/argo-cd",
                    "nublado": "https://nb.data-dev.lsst.cloud/nb",
                }
            ],
        ),
    ] = {}


class Discovery(BaseModel):
    """Service discovery information."""

    applications: Annotated[
        list[str],
        Field(
            title="Phalanx applications",
            description=(
                "Names of all Phalanx applications enabled in the local"
                " environment"
            ),
            examples=[
                ["argocd", "gafaelfawr", "hips", "mobu", "nublado", "wobbly"]
            ],
        ),
    ] = []

    datasets: Annotated[
        list[Dataset],
        Field(
            title="Datasets",
            description="All datasets available in the local environment",
            examples=[["dp02", "dp1"]],
        ),
    ] = []

    urls: Annotated[
        ServiceUrls,
        Field(
            title="Service URLs",
            description="URLs to services available in the local environment",
        ),
    ]
