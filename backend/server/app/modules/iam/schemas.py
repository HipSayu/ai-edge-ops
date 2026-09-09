"""IAM API schemas — user CRUD and auth sessions."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


# --- user CRUD -----------------------------------------------------------
class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    email: str = Field(min_length=3, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=512)
    active: bool = True


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    active: bool | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    active: bool
    created_at: dt.datetime
    updated_at: dt.datetime


# --- auth --------------------------------------------------------------
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
