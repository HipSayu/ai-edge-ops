"""Signs access tokens with RS256. The private key never leaves this service; others get the public key via JWKS."""

import base64
import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from cloud.domain.model.user import User
from shared.tokens import ALGORITHM, ISSUER


log = logging.getLogger("ppe.tokens")


def _load_or_generate(path: Path | None) -> rsa.RSAPrivateKey:
    if path is not None and not path.is_file():
        raise FileNotFoundError(f"CLOUD_JWT_PRIVATE_KEY_PATH points to {path}, which does not exist")
    if path is not None:
        return serialization.load_pem_private_key(path.read_bytes(), password=None)  # type: ignore[return-value]
    # No key configured: a throwaway key. Tokens then stop working after a restart, which is fine for development only.
    log.warning("no JWT private key configured: using a throwaway key (development only)")
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


class RsaTokenIssuer:
    """The TokenIssuer port."""

    def __init__(self, key_path: Path | None, ttl_min: int) -> None:
        self._private = _load_or_generate(key_path)
        self._public = self._private.public_key()
        der = self._public.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.PKCS1)
        self._kid = base64.urlsafe_b64encode(hashlib.sha256(der).digest()[:12]).decode().rstrip("=")
        self._ttl_min = ttl_min

    def issue(self, user: User) -> str:
        now = datetime.now(UTC)
        claims = {
            "iss": ISSUER,
            "sub": str(user.id),
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value,
            "cluster_ids": list(user.cluster_ids),
            "iat": now,
            "exp": now + timedelta(minutes=self._ttl_min),
        }
        return jwt.encode(claims, self._private, algorithm=ALGORITHM, headers={"kid": self._kid})

    def public_pem(self) -> str:
        return self._public.public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    def jwks(self) -> dict:
        key = json.loads(RSAAlgorithm.to_jwk(self._public))
        return {"keys": [{**key, "kid": self._kid, "use": "sig", "alg": ALGORITHM}]}
