import hashlib
import hmac
import uuid

from src.cloud.application.dto.auth_session import AuthSession
from src.cloud.application.dto.register_request import RegisterRequest
from src.cloud.application.ports.access_token_codec import AccessTokenCodec
from src.cloud.application.ports.password_hasher import PasswordHasher
from src.cloud.application.ports.refresh_token_store import RefreshTokenStore
from src.cloud.application.ports.user_repository import UserRepository
from src.cloud.domain.entities.user import User, UserRole
from src.cloud.domain.value_objects.principal import Principal, PrincipalKind
from src.shared.exceptions import AppException, ErrorCode

_INVALID_LOGIN = "Invalid username/email or password"


class AuthService:
    """Password sign-in for people (JWT access + rotating refresh token) and API keys for machine clients.

    No permission model yet: every account is an ADMIN. Registration is open for the first account only,
    later sign-ups need `allow_registration` (admins can always create accounts via /users).
    """

    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: AccessTokenCodec,
        refresh_tokens: RefreshTokenStore,
        service_api_keys: list[str],
        allow_registration: bool = False,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens
        self._refresh_tokens = refresh_tokens
        self._service_key_hashes = [self._digest(k) for k in service_api_keys]
        self._allow_registration = allow_registration

    async def register(self, request: RegisterRequest) -> AuthSession:
        first_user = await self._users.count() == 0
        if not first_user and not self._allow_registration:
            raise AppException(ErrorCode.FORBIDDEN, "Registration is closed; ask an admin for an account")
        user = await self._users.add(
            User(
                id=str(uuid.uuid4()),
                username=request.username,
                email=request.email.lower(),
                password_hash=self._hasher.hash(request.password),
                display_name=request.display_name,
                role=UserRole.ADMIN,
            )
        )
        return await self._session(user)

    async def login(self, login: str, password: str) -> AuthSession:
        user = await self._users.get_by_login(login.strip())
        # Same error for unknown user and wrong password, so accounts cannot be enumerated
        if user is None or not user.can_sign_in() or not self._hasher.verify(user.password_hash, password):
            raise AppException(ErrorCode.UNAUTHORIZED, _INVALID_LOGIN)
        await self._users.touch_login(user.id)
        return await self._session(user)

    async def refresh(self, refresh_token: str) -> AuthSession:
        user_id = await self._refresh_tokens.consume(refresh_token)
        user = await self._users.get(user_id) if user_id else None
        if user is None or not user.can_sign_in():
            raise AppException(ErrorCode.UNAUTHORIZED, "Invalid or expired refresh token")
        return await self._session(user)

    async def logout(self, refresh_token: str) -> None:
        await self._refresh_tokens.consume(refresh_token)

    async def authenticate(self, credential: str | None) -> Principal:
        """Accepts a user access token or a service API key; raises UNAUTHORIZED otherwise."""
        if credential:
            if self._is_service_key(credential):
                return Principal(PrincipalKind.SERVICE, "service", UserRole.ADMIN)
            principal = self._tokens.decode(credential)
            if principal is not None:
                return principal
        raise AppException(ErrorCode.UNAUTHORIZED, "Missing or invalid credentials")

    async def current_user(self, principal: Principal) -> User:
        user = await self._users.get(principal.subject) if principal.is_user else None
        if user is None:
            raise AppException(ErrorCode.NOT_FOUND, "No user behind these credentials (service API key?)")
        return user

    async def _session(self, user: User) -> AuthSession:
        principal = Principal(PrincipalKind.USER, user.id, user.role)
        return AuthSession(
            access_token=self._tokens.encode(principal),
            refresh_token=await self._refresh_tokens.issue(user.id),
            expires_in=self._tokens.ttl_sec,
            user=user,
        )

    def _is_service_key(self, credential: str) -> bool:
        candidate = self._digest(credential)
        return any(hmac.compare_digest(candidate, h) for h in self._service_key_hashes)

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
