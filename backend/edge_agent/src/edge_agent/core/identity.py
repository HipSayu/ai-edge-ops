"""Who/what this agent is — reported with the heartbeat so the control plane
can show version / IP / uptime without the operator filling them in."""

from __future__ import annotations

import socket
import time
from importlib.metadata import PackageNotFoundError, version

_STARTED_MONOTONIC = time.monotonic()


def agent_version() -> str:
    try:
        return version("ai-edge-ops-edge-agent")
    except PackageNotFoundError:  # running from a source checkout without install
        return "0.0.0+src"


def primary_ip() -> str | None:
    """Best-effort LAN IP — the address a UDP socket would use to reach the
    outside world. No packet is actually sent."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 9))  # TEST-NET-1, guaranteed unroutable
        return sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()


def uptime_s() -> float:
    return round(time.monotonic() - _STARTED_MONOTONIC, 1)


__all__ = ["agent_version", "primary_ip", "uptime_s"]
