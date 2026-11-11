"""The id of the request being handled, visible to any code running under it (log lines, calls to other services)."""

import re
import uuid
from contextvars import ContextVar

REQUEST_ID_HEADER = "X-Request-ID"

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_ACCEPTED = re.compile(r"[A-Za-z0-9._\-]{1,64}")  # what a caller may choose: no spaces or control characters in logs


def get_request_id() -> str | None:
    """None outside a request."""
    return _request_id.get()


def new_request_id() -> str:
    return uuid.uuid4().hex


def accept(candidate: str | None) -> str:
    """The caller's id when it is sane (so one id follows a call across services), else a new one."""
    return candidate if candidate and _ACCEPTED.fullmatch(candidate) else new_request_id()


def outgoing_headers() -> dict[str, str]:
    """Headers to put on a call to another service so it logs under the same id."""
    rid = get_request_id()
    return {REQUEST_ID_HEADER: rid} if rid else {}
