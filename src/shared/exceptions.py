"""The one business exception for all of src. Errors differ only by `code`.

src never knows about transports: interfaces map `code` to their own shape (HTTP status, MCP tool error, ...).
"""

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    INVALID_REQUEST = "invalid_request"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    EXTERNAL_SERVICE = "external_service_error"


class AppException(Exception):
    def __init__(self, code: ErrorCode, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
