from dataclasses import dataclass

import jwt

_ALGORITHM = "RS256"
_TYPE = "access"


@dataclass(frozen=True)
class VerifiedToken:
    subject: str
    role: str


class JwtVerifier:
    """Verifies the Cloud's RS256 access tokens with its public key (signature, expiry, issuer, token type)."""

    def __init__(self, public_key_pem: str, issuer: str) -> None:
        self._public_key = public_key_pem
        self._issuer = issuer

    def verify(self, token: str) -> VerifiedToken | None:
        try:
            claims = jwt.decode(
                token, self._public_key, algorithms=[_ALGORITHM], issuer=self._issuer,
                options={"require": ["sub", "exp", "iat", "iss"]},
            )
        except jwt.InvalidTokenError:
            return None
        if claims.get("typ") != _TYPE or "role" not in claims:
            return None
        return VerifiedToken(claims["sub"], claims["role"])
