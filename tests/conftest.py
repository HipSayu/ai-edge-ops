import os
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from src.cloud.config.cloud_settings import CloudSettings

# Tests must not pick up a developer's .env / .env.local (remote DB, API keys, model store...).
CloudSettings.model_config["env_file"] = None
# Auth is always on; tests use a throwaway RSA signing key and one service API key.
_key_file = Path(tempfile.gettempdir()) / "edgeops-test-jwt-private.pem"
if not _key_file.exists():
    _key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _key_file.write_bytes(_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ))
os.environ.setdefault("CLOUD_JWT_PRIVATE_KEY_FILE", str(_key_file))
os.environ.setdefault("CLOUD_API_KEYS", "test-service-key")
