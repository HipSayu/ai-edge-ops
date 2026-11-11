"""Sets up the chat assistant in Dunly: the connector to the cloud's tools, the agent, and the API key the cloud calls with.

    uv run python tools/setup_dunly.py --model openrouter/deepseek-v4-1-flash-1017 \
        --email admin@dunly.local --password ... [--dunly-url http://localhost:8790] \
        [--mcp-url http://host.docker.internal:8100/mcp]

The skills in docs/dunly/skills are sent through Dunly's API (inline skills) and the agent uses them by name.
Safe to run again: the connector, the skills and the agent are updated in place. An API key is created only when `--new-key` is
given (its secret is shown once); put it in apps/interface/cloud/.env as CLOUD_DUNLY_API_KEY.

--mcp-url is where Dunly reaches the cloud's MCP server (/mcp), as seen from Dunly.
The connector forwards `Authorization`: the cloud sends the signed-in user's own token with every chat turn, so each
tool call is made with that user's rights.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for source in ("services/cloud/src", "services/shared/src", "package/edge_link/src", "package/trace_id/src", "."):
    sys.path.insert(0, str(ROOT / source))

from cloud.interface.mcp.tools import TOOLS  # (the tools the cloud's MCP server publishes)

CONNECTOR = "ppe-cloud"
AGENT = "ppe-assistant"
DOCS = ROOT / "docs" / "dunly"
PROMPT = DOCS / "ppe-assistant.md"
SCOPES = ["sessions:read", "sessions:write", "sessions:forward"]


class Dunly:
    def __init__(self, url: str) -> None:
        self._api = url.rstrip("/") + "/api/v1"
        self._token = ""

    def call(self, method: str, path: str, body: dict | None = None, *, ok: tuple[int, ...] = (200, 201)) -> dict:
        request = urllib.request.Request(
            self._api + path, method=method, data=None if body is None else json.dumps(body).encode(),
            headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {self._token}"} if self._token else {})},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as e:
            if e.code in ok:
                return {}
            detail = e.read().decode(errors="replace")[:400]
            raise SystemExit(f"{method} {path} -> {e.code}: {detail}") from e

    def sign_in(self, email: str, password: str) -> None:
        self._token = self.call("POST", "/auth/token", {"email": email, "password": password})["data"]["access_token"]


def skills() -> dict[str, dict[str, str]]:
    """Every skill under docs/dunly/skills/<name>/: its folder's files by relative path (SKILL.md, assets/...)."""
    found = {}
    for skill in sorted((DOCS / "skills").glob("*/SKILL.md")):
        folder = skill.parent
        found[folder.name] = {
            path.relative_to(folder).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(folder.rglob("*"))
            if path.is_file()
        }
    return found


def upsert_skills(dunly: Dunly) -> list[str]:
    """Sends each skill as an inline skill (the files travel in the request), creating or replacing it."""
    existing = {s["name"] for s in dunly.call("GET", "/settings/skills")["data"]}
    names = []
    for name, files in skills().items():
        manifest = {"type": "inline", "name": name, "files": files}
        dunly.call("PUT" if name in existing else "POST", "/settings/skills", {"manifest": manifest})
        names.append(name)
        print(f"skill {name}: {len(files)} files")
    return names


def upsert_connector(dunly: Dunly, mcp_url: str) -> None:
    manifest = {
        "name": CONNECTOR,
        "url": mcp_url,
        # The user's token arrives with each chat turn and goes on as it is. Chatting in Dunly itself sends none: the
        # chat still works and the tools answer "not signed in".
        "auth": {"type": "header", "forward_headers": ["Authorization"]},
    }
    existing = {m["name"] for m in dunly.call("GET", "/settings/mcp-servers")["data"]}
    dunly.call("PUT" if CONNECTOR in existing else "POST", "/settings/mcp-servers", {"manifest": manifest})
    print(f"connector {CONNECTOR}: {mcp_url}")


def upsert_agent(dunly: Dunly, model: str, skill_names: list[str]) -> str:
    changes = sorted(t.name for t in TOOLS if t.changes)
    manifest = {
        "model": {"name": model},
        "instructions": PROMPT.read_text(encoding="utf-8").rstrip(),
        "skills": [{"name": name} for name in skill_names],
        "mcp_servers": [{"name": CONNECTOR, "require_approval_for_tools": changes}],
        # Nobody can answer a question typed into the agent's own prompt: the chat has no place to show it.
        "config": {"ask_user_questions": {"enabled": False}, "web_search": {"enabled": False}},
    }
    agents = {a["name"]: a for a in dunly.call("GET", "/agents?limit=200")["data"]}
    if AGENT in agents:
        agent_id = agents[AGENT]["id"]
        dunly.call("PUT", f"/agents/{agent_id}", {"description": "PPE safety assistant", "manifest": manifest})
    else:
        agent_id = dunly.call("POST", "/agents", {"name": AGENT, "description": "PPE safety assistant", "manifest": manifest})["data"]["id"]
    print(f"agent {AGENT} ({agent_id}): model {model}, approval needed for {len(changes)} tools that change data")
    return agent_id


def new_key(dunly: Dunly, agent_id: str) -> None:
    key = dunly.call("POST", "/api-keys", {"name": "ppe-cloud", "scopes": SCOPES, "agent_ids": [agent_id]})["data"]
    print(f"\nAPI key (shown once): {key['secret']}\n  -> CLOUD_DUNLY_API_KEY in apps/interface/cloud/.env")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True, help="a model name from Dunly's Console > Models")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--dunly-url", default="http://localhost:8790")
    parser.add_argument("--mcp-url", default="http://host.docker.internal:8100/mcp")
    parser.add_argument("--new-key", action="store_true", help="also create the API key the cloud calls with")
    args = parser.parse_args()

    dunly = Dunly(args.dunly_url)
    dunly.sign_in(args.email, args.password)
    upsert_connector(dunly, args.mcp_url)
    agent_id = upsert_agent(dunly, args.model, upsert_skills(dunly))
    if args.new_key:
        new_key(dunly, agent_id)


if __name__ == "__main__":
    main()
