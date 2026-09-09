"""JWT issue/verify for user sessions.

Wraps :class:`dqh.svc_core.security.TokenCodec` with this app's settings and
turns a :class:`TokenError` into a 401 for the API layer.
"""

from __future__ import annotations

import datetime as dt

from dqh.svc_core.security import TokenCodec, TokenError
from fastapi import HTTPException, status

from app.core.config import settings

token_codec = TokenCodec(settings.jwt_secret, settings.jwt_algorithm)


def issue_tokens(user_id: int) -> tuple[str, str, dt.datetime]:
    access, expires_at = token_codec.encode(
        str(user_id), "access", dt.timedelta(minutes=settings.access_token_minutes)
    )
    refresh, _ = token_codec.encode(
        str(user_id), "refresh", dt.timedelta(days=settings.refresh_token_days)
    )
    return access, refresh, expires_at


def decode_token(token: str, expected_type: str) -> int:
    try:
        subject = token_codec.decode(token, expected_type)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        ) from exc
    if not subject.isdigit():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    return int(subject)


__all__ = ["decode_token", "issue_tokens", "token_codec"]
