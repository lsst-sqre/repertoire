"""Exception classes for Repertoire."""

from __future__ import annotations

from typing import Self

from httpx import HTTPError, HTTPStatusError

__all__ = [
    "RepertoireError",
    "RepertoireUrlError",
    "RepertoireValidationError",
    "RepertoireWebError",
]


class RepertoireError(Exception):
    """Base class for Repertoire client exceptions."""


class RepertoireUrlError(RepertoireError):
    """Base URL for Repertoire was not set."""


class RepertoireValidationError(RepertoireError):
    """Discovery information does not pass schema validation."""


class RepertoireWebError(RepertoireError):
    """Exception arising from an HTTP request failure.

    Parameters
    ----------
    message
        Exception string value.
    method
        Method of request.
    url
        URL of the request.
    status
        Status code of failure, if any.
    body
        Body of failure message, if any.

    Attributes
    ----------
    method
        Method of failing request, if available.
    url
        URL of failing request, if available.
    status
        HTTP status of failing request, if available.
    body
        Body of error message from server, if available.
    """

    @classmethod
    def from_exception(cls, exc: HTTPError) -> Self:
        """Create an exception from an HTTPX_ exception.

        Parameters
        ----------
        exc
            Exception from HTTPX.

        Returns
        -------
        RepertoireWebError
            Newly-constructed exception.
        """
        if isinstance(exc, HTTPStatusError):
            status = exc.response.status_code
            method = exc.request.method
            message = f"Status {status} from {method} {exc.request.url}"
            return cls(
                message,
                method=exc.request.method,
                url=str(exc.request.url),
                status=status,
                body=exc.response.text,
            )
        else:
            exc_name = type(exc).__name__
            message = f"{exc_name}: {exc!s}" if str(exc) else exc_name

            # All httpx.HTTPError exceptions have a slot for the request,
            # initialized to None and then sometimes added by child
            # constructors or during exception processing. The request
            # property is a property method that raises RuntimeError if
            # request has not been set, so we can't just check for None. Hence
            # this approach of attempting to use the request and falling back
            # on reporting less data if that raised any exception.
            try:
                return cls(
                    message,
                    method=exc.request.method,
                    url=str(exc.request.url),
                )
            except Exception:
                return cls(message)

    def __init__(
        self,
        message: str,
        *,
        method: str | None = None,
        url: str | None = None,
        status: int | None = None,
        body: str | None = None,
    ) -> None:
        super().__init__(message)
        self._message = message
        self.method = method
        self.url = url
        self.status = status
        self.body = body

    def __str__(self) -> str:
        result = self._message
        if self.body:
            result += f"\nBody:\n{self.body}\n"
        return result
