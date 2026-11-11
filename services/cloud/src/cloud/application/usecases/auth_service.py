"""Signing in, and turning a token back into the viewer it was issued to. The database has the last word:
a disabled or deleted account loses access even while its token is still valid."""

from dataclasses import dataclass

from cloud.application.ports import PasswordHasher, TokenIssuer
from cloud.domain.model.user import User
from shared.errors import Unauthenticated
from shared.text import found
from shared.tokens import TokenVerifier
from shared.viewer import Viewer


@dataclass(frozen=True)
class LoginResult:
    token: str
    user: User


class AuthService:
    def __init__(self, uow, hasher: PasswordHasher, tokens: TokenIssuer) -> None:
        self._uow, self._hasher, self._tokens = uow, hasher, tokens
        self._verifier = TokenVerifier.from_pem(tokens.public_pem())

    def login(self, username: str, password: str) -> LoginResult:
        with self._uow() as uow:
            user = uow.users.by_username(username)
        if user is None or not user.is_active or not self._hasher.verify(password, user.password_hash):
            raise Unauthenticated("Sai tên đăng nhập hoặc mật khẩu")
        return LoginResult(token=self._tokens.issue(user), user=user)

    def authenticate(self, token: str) -> Viewer:
        claims = self._verifier.viewer(token)
        with self._uow() as uow:
            user = uow.users.get(claims.id)
        if user is None or not user.is_active:
            raise Unauthenticated("Tài khoản không tồn tại hoặc đã bị khóa")
        return user.to_viewer()

    def profile(self, viewer: Viewer) -> User:
        with self._uow() as uow:
            return found(uow.users.get(viewer.id), "Không tìm thấy người dùng")
