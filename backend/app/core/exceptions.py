"""Application error hierarchy. Raised by services, mapped to HTTP by handlers."""

from __future__ import annotations


class AppError(Exception):
    status_code = 500
    default_detail = "Internal server error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = 404
    default_detail = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    default_detail = "Resource already exists"


class BusinessRuleError(AppError):
    status_code = 400
    default_detail = "Business rule violated"
