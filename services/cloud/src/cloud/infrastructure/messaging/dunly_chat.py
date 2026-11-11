import json
from collections.abc import Iterator

import httpx

from shared.errors import ServiceUnavailable

OWNER_KEY = "ppe_user"  # session metadata: whose conversation it is, since every user shares one Dunly API key


class DunlyChat:
    """The AgentChat port: a Dunly agent over its REST and SSE API, called with an API key that has the
    sessions:read, sessions:write and sessions:forward scopes. The headers passed with a turn (the signed-in user's
    `Authorization`) go to the connectors that list them in `forward_headers`, so the agent acts as that user."""

    def __init__(
        self, base_url: str, api_key: str, agent: str, timeout_sec: float = 30.0, transport: httpx.BaseTransport | None = None
    ) -> None:
        self._api = base_url.rstrip("/") + "/api/v1"
        self._agent = agent
        self._key = api_key
        self._http = httpx.Client(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(timeout_sec, read=None),  # a turn streams for as long as the agent works
            transport=transport,
        )

    @property
    def agent_name(self) -> str:
        return self._agent

    def open_session(self, owner: int) -> str:
        body = {"agent": {"name": self._agent}, "metadata": {OWNER_KEY: str(owner)}}
        return str(self._json("POST", "/sessions", json=body)["data"]["id"])

    def owns_session(self, session_id: str, owner: int) -> bool:
        try:
            data = self._json("GET", f"/sessions/{session_id}")["data"]
        except ServiceUnavailable:
            return False  # unknown to Dunly, or not reachable: either way there is nothing of the user's to continue
        return (data.get("metadata") or {}).get(OWNER_KEY) == str(owner)

    def run_turn(self, session_id: str, items: list[dict], forward: dict[str, str]) -> Iterator[dict]:
        # One Authorization header holds both credentials: Dunly takes the one with its own prefix and passes on the rest.
        credentials = [f"Bearer {self._key}", *filter(None, [forward.get("Authorization")])]
        headers = {**forward, "Authorization": ", ".join(credentials)}
        body = {"input": items, "stream": True}
        try:
            with self._http.stream(
                "POST", f"{self._api}/sessions/{session_id}/turns", json=body, headers=headers
            ) as response:
                if response.is_error:
                    response.read()
                    raise ServiceUnavailable(_detail(response))
                for line in response.iter_lines():
                    if line.startswith("data:"):
                        yield json.loads(line[5:])
        except httpx.HTTPError as e:
            raise ServiceUnavailable(f"Không gọi được trợ lý: {e}") from e

    def _json(self, method: str, path: str, **kwargs) -> dict:
        try:
            response = self._http.request(method, self._api + path, **kwargs)
        except httpx.HTTPError as e:
            raise ServiceUnavailable(f"Không gọi được trợ lý: {e}") from e
        if response.is_error:
            raise ServiceUnavailable(_detail(response))
        return response.json()


def _detail(response: httpx.Response) -> str:
    try:
        message = response.json()["error"]["message"]
    except (ValueError, KeyError, TypeError):
        message = response.text[:200]
    return f"Trợ lý trả lỗi {response.status_code}: {message}"
