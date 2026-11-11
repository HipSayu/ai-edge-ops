"""Turns the agent's events into what the web chat reads: (name, data) pairs.

    reasoning {content} | token {content} | tool_start {name} | tool_end {} | approval_required {id, summary, tool, args}
    report {url} | done {session_id, reply} | error {message}

The agent streams the text of its main thread as deltas, groups the tool calls of one step into one message, and pauses
a turn when a call needs the user's approval. Sub-agent threads are not shown."""

import json
from dataclasses import dataclass

from cloud.application.usecases.chat_files_service import REPORT_URL_PREFIX

Event = tuple[str, dict]
MAIN = "main"


@dataclass(frozen=True)
class PendingCall:
    id: str
    tool: str
    args: dict
    summary: str


def _summary(tool: str, args: dict) -> str:
    shown = ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in args.items() if v is not None)
    return f"{tool}({shown})"


class ChatEvents:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.pending: list[PendingCall] = []  # calls the user has to answer, once the turn pauses
        self._calls: dict[str, PendingCall] = {}
        self._asked: list[str] = []
        self._streamed = ""
        self._answer = ""
        self._failed = False

    def feed(self, event: dict) -> list[Event]:
        kind = event.get("type")
        if kind == "turn.done":
            return self._turn_done(event.get("state") or {})
        if event.get("thread_id", MAIN) != MAIN:
            return []
        if kind == "model.message.delta":
            thought = event.get("reasoning_content") or ""
            text = event.get("content") or ""
            self._streamed += text
            return [
                *([("reasoning", {"content": thought})] if thought else []),
                *([("token", {"content": text})] if text else []),
            ]
        if kind == "model.message":
            return self._message(event)
        if kind == "tool.response":
            return [("tool_end", {}), *self._report(event)]
        if kind == "tool.approval_required":
            self._asked += [ref["id"] for ref in event.get("tool_calls") or []]
        return []

    def finish(self) -> list[Event]:
        """The stream ended: a paused turn announces what waits for the user, then the turn is over."""
        if self._failed:
            return []
        self.pending = [self._calls[i] for i in self._asked if i in self._calls]
        out: list[Event] = [
            ("approval_required", {"id": c.id, "summary": c.summary, "tool": c.tool, "args": c.args})
            for c in self.pending
        ]
        return [*out, ("done", {"session_id": self.session_id, "reply": self._answer or self._streamed})]

    def _report(self, event: dict) -> list[Event]:
        """The link a finished report comes back with, so the page can offer the download."""
        call = self._calls.get(event.get("tool_call_id", ""))
        if call is None or call.tool != "export_safety_report":
            return []
        url = _json_of(event.get("content")).get("url")
        return [("report", {"url": url})] if isinstance(url, str) and url.startswith(REPORT_URL_PREFIX) else []

    def _message(self, event: dict) -> list[Event]:
        out: list[Event] = []
        for call in event.get("tool_calls") or []:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"].get("arguments") or "{}")
            except ValueError:
                args = {}
            self._calls[call["id"]] = PendingCall(call["id"], name, args, _summary(name, args))
            out.append(("tool_start", {"name": name}))
        if not out and event.get("content"):
            self._answer = event["content"]
        return out

    def _turn_done(self, state: dict) -> list[Event]:
        if state.get("status") == "error":
            self._failed = True
            return [("error", {"message": state.get("message") or "Trợ lý gặp lỗi"})]
        return []


def _json_of(content: str | None) -> dict:
    """What a tool answered as an object. An MCP tool's answer arrives as a list of text blocks around its JSON."""
    try:
        value = json.loads(content or "{}")
        if isinstance(value, list):
            value = json.loads("".join(b.get("text", "") for b in value if isinstance(b, dict)) or "{}")
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}
