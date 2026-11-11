"""The chat with the assistant. The agent lives in Dunly; this service is the door to it for the signed-in user.

The user's own token goes with every turn, so the agent reads and changes data with that user's rights: the cloud's
tools check the role again. A change the agent proposes waits here until the user approves it in the chat."""

import itertools
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field

from cloud.application.dto.chat_events import MAIN, ChatEvents, Event, PendingCall
from cloud.application.ports import AgentChat
from cloud.application.usecases.chat_files_service import ChatImageService
from shared.errors import Invalid, NotAllowed, ServiceUnavailable
from shared.viewer import Viewer

MAX_MESSAGE_CHARS = 8000


@dataclass(frozen=True)
class ChatStarted:
    stream_id: str
    session_id: str


@dataclass
class _Run:
    viewer_id: int
    session_id: str
    items: list[dict]
    token: str


@dataclass
class ChatService:
    agent: AgentChat | None
    images: ChatImageService | None = None
    _runs: dict[str, _Run] = field(default_factory=dict)
    _waiting: dict[tuple[int, str], tuple[str, PendingCall]] = field(default_factory=dict)  # (viewer, call) -> session
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _ids: Iterator[int] = field(default_factory=itertools.count)

    def models(self) -> tuple[str, list[str]]:
        name = self._agent().agent_name
        return name, [name]

    def start(
        self, viewer: Viewer, token: str, message: str, session_id: str | None, image_ids: list[str] | None = None
    ) -> ChatStarted:
        """Checks the request now, so a mistake fails here as a plain error; the turn runs when its events are read."""
        agent = self._agent()
        message = message.strip()
        if not message:
            raise Invalid("Tin nhắn trống")
        if len(message) > MAX_MESSAGE_CHARS:
            raise Invalid(f"Tin nhắn quá dài (tối đa {MAX_MESSAGE_CHARS} ký tự)")
        for image_id in image_ids or []:  # the agent learns of a picture by its id and looks at it with detect_ppe
            if self.images is None or not self.images.owns(viewer, image_id):
                raise NotAllowed("Không tìm thấy ảnh đính kèm")
            message += f"\n[Ảnh đính kèm: image_id={image_id}]"
        if session_id is None:
            session_id = agent.open_session(viewer.id)
        elif not agent.owns_session(session_id, viewer.id):
            raise NotAllowed("Không tìm thấy cuộc trò chuyện")
        with self._lock:
            stream_id = f"stream-{next(self._ids)}"
            self._runs[stream_id] = _Run(viewer.id, session_id, [{"type": "user.message", "content": message}], token)
        return ChatStarted(stream_id, session_id)

    def events(self, viewer: Viewer, stream_id: str) -> Iterator[Event]:
        """The events of a started turn as the agent produces them. Readable once."""
        with self._lock:
            run = self._runs.get(stream_id)
            if run is None or run.viewer_id != viewer.id:
                raise NotAllowed("Không tìm thấy luồng trả lời hoặc đã được đọc")
            del self._runs[stream_id]
        return self._stream(run)

    def decide(self, viewer: Viewer, token: str, call_id: str, approve: bool) -> str:
        """The user's answer to a change the agent proposed. The agent applies it with the user's token."""
        agent = self._agent()
        with self._lock:
            waiting = self._waiting.pop((viewer.id, call_id), None)
        if waiting is None:
            raise NotAllowed("Không tìm thấy đề xuất hoặc đã được xử lý")
        session_id, call = waiting
        approval = {"status": "allow"} if approve else {"status": "deny", "reason": "Người dùng từ chối"}
        item = {"type": "user.tool_approval", "thread_id": MAIN, "tool_call_id": call_id, "approval": approval}
        translator = ChatEvents(session_id)
        error = None
        for raw in agent.run_turn(session_id, [item], {"Authorization": f"Bearer {token}"}):
            for name, data in translator.feed(raw):
                if name == "error":
                    error = data["message"]
        if error:
            raise ServiceUnavailable(error)
        done = dict(translator.finish()).get("done", {})
        return done.get("reply") or (f"Đã thực hiện: {call.summary}" if approve else f"Đã hủy: {call.summary}")

    def _stream(self, run: _Run) -> Iterator[Event]:
        translator = ChatEvents(run.session_id)
        try:
            for raw in self._agent().run_turn(run.session_id, run.items, {"Authorization": f"Bearer {run.token}"}):
                yield from translator.feed(raw)
        except Exception as e:  # noqa: BLE001 - the stream is already open: report the failure as an event
            yield "error", {"message": f"Assistant error: {e}"}
            return
        events = translator.finish()
        with self._lock:
            for call in translator.pending:
                self._waiting[(run.viewer_id, call.id)] = (run.session_id, call)
        yield from events

    def _agent(self) -> AgentChat:
        if self.agent is None:
            raise ServiceUnavailable("Chưa cấu hình trợ lý (CLOUD_DUNLY_URL, CLOUD_DUNLY_API_KEY)")
        return self.agent
