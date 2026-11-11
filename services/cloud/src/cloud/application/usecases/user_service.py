"""Accounts: create, change, delete. The role needed to call these is checked at the entry point."""

from cloud.application.ports import PasswordHasher
from cloud.domain.model.user import User
from shared.errors import Conflict, Invalid
from shared.roles import Role
from shared.text import found


def _role(value: str) -> Role:
    try:
        return Role(value)
    except ValueError:
        raise Invalid("Vai trò không hợp lệ")


class UserService:
    def __init__(self, uow, hasher: PasswordHasher) -> None:
        self._uow, self._hasher = uow, hasher

    def all(self) -> list[User]:
        with self._uow() as uow:
            return uow.users.list()

    def create(
        self, *, username: str, password: str | None, full_name: str, role: str, is_active: bool, cluster_ids: list[int]
    ) -> User:
        with self._uow() as uow:
            if uow.users.by_username(username):
                raise Conflict("Tên đăng nhập đã tồn tại")
            parsed_role = _role(role)
            if not password:
                raise Invalid("Cần mật khẩu khi tạo tài khoản")
            user = User(
                username=username, password_hash=self._hasher.hash(password), full_name=full_name,
                role=parsed_role, is_active=is_active, cluster_ids=self._existing(uow, cluster_ids),
            )
            return uow.users.add(user)

    def update(
        self, user_id: int, *, password: str | None, full_name: str, role: str, is_active: bool, cluster_ids: list[int]
    ) -> User:
        with self._uow() as uow:
            user = found(uow.users.get(user_id), "Không tìm thấy người dùng")
            user.update_profile(
                full_name=full_name, role=_role(role), is_active=is_active, cluster_ids=self._existing(uow, cluster_ids)
            )
            if password:
                user.password_hash = self._hasher.hash(password)
            uow.users.save(user)
            return user

    def delete(self, user_id: int) -> None:
        with self._uow() as uow:
            found(uow.users.get(user_id), "Không tìm thấy người dùng")
            uow.users.remove(user_id)

    @staticmethod
    def _existing(uow, cluster_ids: list[int]) -> list[int]:
        """Unknown cluster ids are dropped, as the form may hold a cluster deleted a moment ago."""
        known = {c.id for c in uow.clusters.list()}
        return [i for i in cluster_ids if i in known]
