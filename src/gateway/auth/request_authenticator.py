from collections.abc import Mapping

from src.gateway.auth.jwt_verifier import JwtVerifier

# Reachable without credentials: sign-in endpoints, health and API docs
PUBLIC_PATHS = ("/health", "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh")
PUBLIC_PREFIXES = ("/api/docs", "/api/redoc", "/api/openapi.json")
IDENTITY_HEADERS = ("x-auth-subject", "x-auth-role")


class Unauthorized(Exception):
    pass


class RequestAuthenticator:
    """Decides, at the gateway, whether a request may reach an upstream and with which identity.

    - A user access token (JWT, from `Authorization: Bearer` or `?token=` on WebSockets) is verified here with
      the Cloud's public key; the upstream receives X-Auth-Subject / X-Auth-Role.
    - A service API key (X-API-Key, or a non-JWT bearer) is passed through: the upstream owns the key list.
    - Public paths pass as they are. Anything else is rejected.
    """

    def __init__(self, verifier: JwtVerifier) -> None:
        self._verifier = verifier

    def identity(self, path: str, headers: Mapping[str, str], query: Mapping[str, str]) -> dict[str, str]:
        """Identity headers to add upstream ({} for public or API-key requests); raises Unauthorized."""
        bearer = self._bearer(headers) or query.get("token")
        if bearer and self._is_jwt(bearer):
            verified = self._verifier.verify(bearer)
            if verified is None:
                raise Unauthorized("invalid or expired access token")
            return {"X-Auth-Subject": verified.subject, "X-Auth-Role": verified.role}
        if bearer or headers.get("x-api-key") or query.get("api_key") or self._is_public(path):
            return {}
        raise Unauthorized("missing credentials")

    @staticmethod
    def _bearer(headers: Mapping[str, str]) -> str | None:
        value = headers.get("authorization", "")
        if not value.lower().startswith("bearer "):
            return None
        return value[7:].strip() or None

    @staticmethod
    def _is_jwt(token: str) -> bool:
        return token.count(".") == 2

    @staticmethod
    def _is_public(path: str) -> bool:
        return path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES)
