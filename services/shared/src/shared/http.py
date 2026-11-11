"""HTTP glue every FastAPI service needs: the bearer token, and the mapping from domain errors to status codes."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shared.errors import (
    Conflict,
    DomainError,
    Forbidden,
    Invalid,
    NotAllowed,
    ServiceUnavailable,
    Unauthenticated,
)

_STATUS: tuple[tuple[type[DomainError], int], ...] = (
    (Unauthenticated, 401),
    (Forbidden, 403),
    (NotAllowed, 404),
    (Conflict, 409),
    (Invalid, 400),
    (ServiceUnavailable, 503),
)


def status_for(error: DomainError) -> int:
    return next((code for kind, code in _STATUS if isinstance(error, kind)), 400)


def register_error_handlers(app: FastAPI) -> None:
    async def handle(_: Request, error: DomainError) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=status_for(error))

    app.add_exception_handler(DomainError, handle)


def bearer_token(request: Request) -> str:
    """The token from `Authorization: Bearer`. Never from the URL: a URL ends up in logs, history and shared links."""
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer ") and header[7:].strip():
        return header[7:].strip()
    raise Unauthenticated("Cần đăng nhập")
