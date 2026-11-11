import hashlib
import hmac
import os

ITERATIONS = 310_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations))
    except ValueError:
        return False
    return hmac.compare_digest(digest, bytes.fromhex(digest_hex))


class Pbkdf2PasswordHasher:
    """The PasswordHasher port."""

    def hash(self, password: str) -> str:
        return hash_password(password)

    def verify(self, password: str, stored: str) -> bool:
        return verify_password(password, stored)
