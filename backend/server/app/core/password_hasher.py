"""The process-wide Argon2 password hasher."""

from __future__ import annotations

from dqh.svc_core.security import PasswordHasher

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    return password_hasher.verify(password, password_hash)


__all__ = ["hash_password", "password_hasher", "verify_password"]
