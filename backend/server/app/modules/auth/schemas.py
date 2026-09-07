from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=512)


class RefreshRequest(BaseModel):
    refreshToken: str = Field(min_length=20)


class UserSession(BaseModel):
    id: int
    name: str
    email: str
    active: bool
    permissions: list[str]


class AuthTokens(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "bearer"
    expiresAt: dt.datetime


class AuthSession(AuthTokens):
    user: UserSession