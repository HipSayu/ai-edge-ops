"""Application logging setup using svc_core middleware helpers."""

from __future__ import annotations

import logging

from dqh.svc_core.middleware.logging import DEFAULT_FORMAT, install_request_id_log_filter

_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    logging.basicConfig(level=level, format=DEFAULT_FORMAT)
    install_request_id_log_filter()
    _CONFIGURED = True
