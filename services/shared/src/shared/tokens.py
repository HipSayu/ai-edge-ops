"""Verifying access tokens. Only cloud signs them (RS256, private key). Everyone else holds the public key,
either as a PEM or fetched from cloud's JWKS endpoint, and turns the claims back into a Viewer."""

from collections.abc import Callable
from typing import Any

import jwt

from shared.errors import Unauthenticated
from shared.roles import Role
from shared.viewer import Viewer

ISSUER = "cloud"
ALGORITHM = "RS256"

KeySource = Callable[[str], Any]  # token -> key to verify it with


class TokenVerifier:
    def __init__(self, key: KeySource) -> None:
        self._key = key

    @classmethod
    def from_pem(cls, public_pem: str) -> "TokenVerifier":
        return cls(lambda _token: public_pem)

    @classmethod
    def from_jwks(cls, jwks_url: str) -> "TokenVerifier":
        client = jwt.PyJWKClient(jwks_url, cache_keys=True)
        return cls(lambda token: client.get_signing_key_from_jwt(token).key)

    def viewer(self, token: str) -> Viewer:
        """Raises Unauthenticated when the token is forged, expired or malformed."""
        try:
            claims = jwt.decode(token, self._key(token), algorithms=[ALGORITHM], issuer=ISSUER)
            return Viewer(
                id=int(claims["sub"]),
                username=claims["username"],
                full_name=claims.get("full_name", ""),
                role=Role(claims["role"]),
                cluster_ids=tuple(int(i) for i in claims.get("cluster_ids", [])),
            )
        except (jwt.InvalidTokenError, jwt.PyJWKClientError, KeyError, ValueError) as e:
            raise Unauthenticated("Phiên đăng nhập không hợp lệ") from e
