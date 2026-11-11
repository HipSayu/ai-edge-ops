"""Tokens: cloud signs RS256 and publishes the public key; other services verify with that key only."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from cloud.interface.rest.app import create_app
from cloud.bootstrap.settings import Settings
from shared.errors import Unauthenticated
from shared.tokens import TokenVerifier


@pytest.fixture
def client(tmp_path):
    settings = Settings(
        data_dir=tmp_path, video_dir=tmp_path / "video",
        database_url=f"sqlite:///{(tmp_path / 't.db').as_posix()}",
    )
    with TestClient(create_app(settings)) as c:
        yield c


def test_login_token_verifies_with_published_key(client):
    token = client.post("/api/auth/login", json={"username": "operator1", "password": "demo123"}).json()["access_token"]
    jwks = client.get("/.well-known/jwks.json").json()
    key = jwt.PyJWKSet.from_dict(jwks)  # the same key any service would load
    viewer = TokenVerifier(lambda t: key[jwt.get_unverified_header(t)["kid"]].key).viewer(token)
    assert viewer.username == "operator1"
    assert viewer.role.value == "OPERATOR"


def test_jwks_has_one_rs256_key_with_kid(client):
    keys = client.get("/.well-known/jwks.json").json()["keys"]
    assert len(keys) == 1
    assert keys[0]["alg"] == "RS256" and keys[0]["kid"] and "d" not in keys[0]  # no private part


def test_hs256_token_signed_with_a_guess_is_rejected(client):
    forged = jwt.encode({"iss": "cloud", "sub": "1", "username": "admin", "role": "ADMIN"}, "guess", algorithm="HS256")
    with pytest.raises(Unauthenticated):
        TokenVerifier.from_pem(client.app.state.container.tokens.public_pem()).viewer(forged)


def test_expired_token_is_rejected(client):
    tokens = client.app.state.container.tokens
    claims = {"iss": "cloud", "sub": "1", "username": "admin", "role": "ADMIN",
              "exp": datetime.now(UTC) - timedelta(minutes=1)}
    private = tokens._private  # test-only: mint an already expired token with the real key
    expired = jwt.encode(claims, private, algorithm="RS256")
    with pytest.raises(Unauthenticated):
        TokenVerifier.from_pem(tokens.public_pem()).viewer(expired)


def test_token_from_another_issuer_is_rejected(client):
    tokens = client.app.state.container.tokens
    other = jwt.encode({"iss": "someone-else", "sub": "1", "username": "x", "role": "ADMIN"},
                       tokens._private, algorithm="RS256")
    with pytest.raises(Unauthenticated):
        TokenVerifier.from_pem(tokens.public_pem()).viewer(other)
