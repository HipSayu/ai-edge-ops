"""Helpers for validating edge protocol metadata."""

from __future__ import annotations

from dqh.svc_core.contracts.messaging import Envelope


def device_id_from_envelope(envelope: Envelope) -> str:
    """The device ID carried by an edge message source (the box's DEVICE_ID)."""
    if not envelope.source:
        raise ValueError(f"bad device source {envelope.source!r}")
    return str(envelope.source)


__all__ = ["device_id_from_envelope"]