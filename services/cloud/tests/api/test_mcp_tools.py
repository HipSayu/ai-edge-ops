"""The MCP tools act as the caller: the token decides what each tool may see or change."""

import json

import pytest
from fastapi.testclient import TestClient
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from cloud.interface.rest.app import create_app
from cloud.bootstrap.settings import Settings
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import socket
import threading
import time
import uvicorn


def _key_file(folder):
    """One signing key on disk, so a second app over the same data accepts the first app's tokens."""
    path = folder / "key.pem"
    path.write_bytes(rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    return path


@pytest.fixture
def settings(tmp_path):
    return Settings(
        data_dir=tmp_path, video_dir=tmp_path / "video",
        database_url=f"sqlite:///{(tmp_path / 'cloud.db').as_posix()}", jwt_private_key_path=_key_file(tmp_path),
    )


@pytest.fixture
def app(settings):
    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture
def mcp_url(app, settings):  # `app` first: it creates the database; the server is a second app over the same data
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(
        create_app(settings), host="127.0.0.1", port=port, log_level="warning"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    while not server.started:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}/mcp"
    server.should_exit = True
    t.join(5)


def _login(app, username, password="demo123") -> str:
    return f"Bearer {app.post('/api/auth/login', json={'username': username, 'password': password}).json()['access_token']}"


async def _call(url, authorization, tool, args=None):
    headers = {"Authorization": authorization} if authorization else {}
    async with streamablehttp_client(url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(tool, args or {})


async def test_read_tool_returns_what_the_caller_may_see(mcp_url, app):
    result = await _call(mcp_url, _login(app, "admin", "admin123"), "list_clusters")
    assert not result.isError
    assert [c["name"] for c in json.loads(result.content[0].text)] == ["Công trường mẫu"]


async def test_viewer_may_not_change_anything(mcp_url, app):
    result = await _call(mcp_url, _login(app, "viewer1"), "create_cluster", {"name": "Lậu"})
    assert result.isError and "403" in result.content[0].text


async def test_call_without_a_token_is_refused(mcp_url):
    result = await _call(mcp_url, None, "list_clusters")
    assert result.isError and "401" in result.content[0].text


async def test_unknown_camera_is_404(mcp_url, app):
    result = await _call(mcp_url, _login(app, "admin", "admin123"), "camera_status", {"camera_id": 99999})
    assert result.isError and "404" in result.content[0].text
