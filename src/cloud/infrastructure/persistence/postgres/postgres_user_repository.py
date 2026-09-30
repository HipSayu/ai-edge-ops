from __future__ import annotations

import asyncpg

from src.cloud.domain.entities.user import User
from src.cloud.infrastructure.persistence.postgres.postgres_repository import PostgresRepository
from src.shared.exceptions import AppException, ErrorCode


class PostgresUserRepository(PostgresRepository[User]):
    entity = User

    async def add(self, user: User) -> User:
        try:
            return await self._one(
                """
                INSERT INTO users (id, username, email, display_name, password_hash, role, status)
                VALUES ($1::uuid, $2, $3, $4, $5, $6::user_role, $7::user_status)
                RETURNING *
                """,
                user.id, user.username, user.email, user.display_name, user.password_hash,
                user.role.value, user.status.value,
            )
        except asyncpg.UniqueViolationError as exc:
            raise AppException(ErrorCode.CONFLICT, "Username or email already registered") from exc

    async def get(self, user_id: str) -> User | None:
        try:
            return await self._one("SELECT * FROM users WHERE id = $1::uuid", user_id)
        except asyncpg.DataError:  # not a UUID
            return None

    async def get_by_login(self, login: str) -> User | None:
        return await self._one(
            "SELECT * FROM users WHERE lower(email) = lower($1) OR lower(username) = lower($1)", login
        )

    async def count(self) -> int:
        return await self._db.pool.fetchval("SELECT count(*) FROM users")

    async def list(self) -> list[User]:
        return await self._many("SELECT * FROM users ORDER BY created_at")

    async def save(self, user: User) -> User:
        return await self._one(
            """
            UPDATE users SET display_name = $2, role = $3::user_role, status = $4::user_status, password_hash = $5
            WHERE id = $1::uuid
            RETURNING *
            """,
            user.id, user.display_name, user.role.value, user.status.value, user.password_hash,
        )

    async def touch_login(self, user_id: str) -> None:
        await self._execute("UPDATE users SET last_login_at = NOW() WHERE id = $1::uuid", user_id)
