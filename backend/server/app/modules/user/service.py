"""User management use-cases."""

from __future__ import annotations

from dqh.svc_core.contracts.errors import ConflictError, NotFoundError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import hash_password
from app.modules.user.models import User
from app.modules.user.schemas import UserCreate, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_users(self) -> list[User]:
        return list((await self.session.scalars(select(User).order_by(User.name))).all())

    async def create_user(self, data: UserCreate) -> User:
        if await self.session.scalar(select(User).where(User.email == data.email)):
            raise ConflictError(f"user '{data.email}' already exists")
        values = data.model_dump(exclude={"password"})
        user = User(**values)
        if data.password:
            user.password_hash = hash_password(data.password)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user(self, user_id: int) -> User:
        user = await self.session.get(User, user_id)
        if user is None:
            raise NotFoundError(f"user {user_id} not found")
        return user

    async def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = await self.get_user(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self.session.commit()
        await self.session.refresh(user)
        return user
