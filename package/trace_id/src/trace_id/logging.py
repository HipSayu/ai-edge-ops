"""Log setup: every line carries the service name and the id of the request it belongs to."""

import logging
import os

from trace_id.context import get_request_id

FORMAT = "%(asctime)s %(levelname)-7s %(service)s %(request_id)s %(name)s: %(message)s"


class RequestContextFilter(logging.Filter):
    """Adds `request_id` ("-" outside a request) and `service` to every record that passes."""

    def __init__(self, service: str) -> None:
        super().__init__()
        self.service = service

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        record.service = self.service
        return True


def configure_logging(service: str, level: str | None = None) -> None:
    """Call once at process start (main.py). Level from the argument or LOG_LEVEL, default INFO. Safe to call twice."""
    root = logging.getLogger()
    if any(getattr(h, "_trace_id", False) for h in root.handlers):
        return
    handler = logging.StreamHandler()
    handler._trace_id = True  # type: ignore[attr-defined]
    handler.setFormatter(logging.Formatter(FORMAT))
    handler.addFilter(RequestContextFilter(service))
    root.addHandler(handler)
    root.setLevel((level or os.environ.get("LOG_LEVEL", "INFO")).upper())
