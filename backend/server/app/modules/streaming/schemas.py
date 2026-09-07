"""Streaming API schemas.

We don't run any media logic ourselves — MediaMTX is the WHIP (ingest) / WHEP
(egress) server and does the actual SFU/ICE/NAT-traversal work. This module
only issues short-lived, path-scoped tokens that MediaMTX validates against
our ``/streaming/auth`` webhook before letting a publish or read through.
"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class StreamTokenOut(BaseModel):
    url: str  # WHIP or WHEP endpoint to POST an SDP offer to
    path: str  # MediaMTX path, e.g. "cam_12"
    token: str  # bearer token to send as `Authorization: Bearer <token>`
    expires_at: dt.datetime


class StreamAuthCheck(BaseModel):
    """Payload MediaMTX POSTs to our auth webhook. See:
    https://mediamtx.org/docs/features/authentication
    """

    user: str = ""
    password: str = ""
    token: str = ""
    ip: str = ""
    action: str = ""  # publish | read | playback | api | metrics | pprof
    path: str = ""
    protocol: str = ""
    id: str = ""
    query: str = ""
    userAgent: str = ""


__all__ = ["StreamAuthCheck", "StreamTokenOut"]
