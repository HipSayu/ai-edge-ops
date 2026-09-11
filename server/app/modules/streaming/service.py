"""Issues and verifies short-lived MediaMTX WHIP/WHEP tokens.

No media state lives here — MediaMTX owns rooms/tracks/ICE. This service only
mints a token scoped to (path, action, ttl) and later checks one against the
same claims from the ``/streaming/auth`` webhook MediaMTX calls before it lets
a publish or read proceed.
"""

from __future__ import annotations

import datetime as dt

import jwt

from app.core.config import Settings
from app.core.config import settings as default_settings
from app.modules.streaming.schemas import StreamTokenOut

TOKEN_TYPE = "stream"


class StreamingService:
    def __init__(self, settings: Settings = default_settings) -> None:
        self.settings = settings

    @staticmethod
    def camera_path(camera_id: int) -> str:
        return f"cam_{camera_id}"

    def issue_publish_token(self, camera_id: int) -> StreamTokenOut:
        return self._issue(self.camera_path(camera_id), "publish")

    def issue_view_token(self, camera_id: int) -> StreamTokenOut:
        return self._issue(self.camera_path(camera_id), "read")

    def verify(self, token: str, *, path: str, action: str) -> bool:
        try:
            payload = jwt.decode(
                token, self.settings.jwt_secret, algorithms=[self.settings.jwt_algorithm]
            )
        except jwt.PyJWTError:
            return False
        return (
            payload.get("type") == TOKEN_TYPE
            and payload.get("path") == path
            and payload.get("action") == action
        )

    def _issue(self, path: str, action: str) -> StreamTokenOut:
        now = dt.datetime.now(dt.timezone.utc)
        expires_at = now + dt.timedelta(seconds=self.settings.stream_token_seconds)
        token = jwt.encode(
            {"type": TOKEN_TYPE, "path": path, "action": action, "iat": now, "exp": expires_at},
            self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm,
        )
        if action == "publish":
            url = f"{self.settings.mediamtx_whip_url}/{path}/whip"
        else:
            url = f"{self.settings.mediamtx_whep_url}/{path}/whep"
        return StreamTokenOut(url=url, path=path, token=token, expires_at=expires_at)


__all__ = ["StreamingService"]
