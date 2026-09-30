import time

import jwt
from cryptography.hazmat.primitives import serialization

from src.cloud.domain.entities.user import UserRole
from src.cloud.domain.value_objects.principal import Principal, PrincipalKind

_ALGORITHM = "RS256"
_TYPE = "access"


class JwtAccessTokenCodec:
    """RS256 JWT access tokens carrying the user id (`sub`) and role.

    The Cloud signs with the private key; anyone holding the public key (the API gateway) can verify.
    """

    def __init__(self, private_key_pem: str, ttl_sec: int, issuer: str = "edgeops-cloud") -> None:
        self._private_key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
        self._public_key = self._private_key.public_key()
        self._ttl_sec = ttl_sec
        self._issuer = issuer

    @property
    def ttl_sec(self) -> int:
        return self._ttl_sec

    def encode(self, principal: Principal) -> str:
        now = int(time.time())
        claims = {
            "sub": principal.subject, "role": principal.role.value, "typ": _TYPE,
            "iss": self._issuer, "iat": now, "exp": now + self._ttl_sec,
        }
        return jwt.encode(claims, self._private_key, algorithm=_ALGORITHM)

    def decode(self, token: str) -> Principal | None:
        try:
            claims = jwt.decode(
                token, self._public_key, algorithms=[_ALGORITHM], issuer=self._issuer,
                options={"require": ["sub", "exp", "iat", "iss"]},
            )
            if claims.get("typ") != _TYPE:
                return None
            return Principal(PrincipalKind.USER, claims["sub"], UserRole(claims["role"]))
        except (jwt.InvalidTokenError, KeyError, ValueError):
            return None
