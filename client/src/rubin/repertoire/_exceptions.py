"""Exception classes for Repertoire."""

from safir.slack.blockkit import SlackException, SlackWebException

__all__ = [
    "RepertoireError",
    "RepertoireUrlError",
    "RepertoireValidationError",
    "RepertoireWebError",
]


class RepertoireError(SlackException):
    """Base class for Repertoire client exceptions."""


class RepertoireUrlError(RepertoireError):
    """Base URL for Repertoire was not set."""

    def __init__(self) -> None:
        super().__init__("REPERTOIRE_BASE_URL not set in environment")


class RepertoireValidationError(RepertoireError):
    """Discovery information does not pass schema validation."""


class RepertoireWebError(SlackWebException, RepertoireError):
    """An HTTP request failed."""
