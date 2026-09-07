"""Helpers for validating edge protocol metadata."""

from __future__ import annotations

from dqh.svc_core.contracts.messaging import Envelope


def device_id_from_envelope(envelope: Envelope) -> int:
    """Read the numeric device ID carried by an edge message source."""
    try:
        return int(envelope.source)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"bad device source {envelope.source!r}") from exc


__all__ = ["device_id_from_envelope"]