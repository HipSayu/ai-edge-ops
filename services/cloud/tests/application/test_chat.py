"""The chat door to the Dunly agent: events translated for the web, the user's token passed as context, approvals."""

import json

import httpx
import pytest

from cloud.application.dto.chat_events import ChatEvents
from cloud.application.usecases.chat_service import ChatService
from cloud.infrastructure.messaging.dunly_chat import DunlyChat
from shared.errors import Invalid, NotAllowed, ServiceUnavailable
from shared.roles import Role
from shared.viewer import Viewer


def viewer(user_id: int = 1) -> Viewer:
    return Viewer(user_id, "an", "An", Role.ADMIN, ())


def call(call_id: str, name: str, **args) -> dict:
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


READ_THEN_ANSWER = [
    {"type": "model.message", "thread_id": "main", "content": None, "tool_calls": [call("c1", "list_violations", limit=5)]},
    {"type": "tool.response", "thread_id": "main", "tool_call_id": "c1", "content": "[]"},
    {"type": "model.message.delta", "thread_id": "main", "content": "Không có "},
    {"type": "model.message.delta", "thread_id": "main", "content": "vi phạm."},
    {"type": "model.message", "thread_id": "main", "content": "Không có vi phạm.", "tool_calls": []},
    {"type": "turn.done", "state": {"status": "done"}},
]

PROPOSE = [
    {"type": "model.message", "thread_id": "main", "content": None, "tool_calls": [call("c9", "delete_camera", camera_id=3)]},
    {"type": "tool.approval_required", "thread_id": "main", "tool_calls": [{"id": "c9", "source_event_id": "e1"}]},
    {"type": "turn.update", "state": {"status": "paused"}},
]


class FakeAgent:
    agent_name = "ppe-assistant"

    def __init__(self, *scripts: list[dict]) -> None:
        self.scripts = list(scripts)
        self.sent: list[tuple[str, list[dict], dict]] = []
        self.owners: dict[str, int] = {}

    def open_session(self, owner: int) -> str:
        self.owners["ses_1"] = owner
        return "ses_1"

    def owns_session(self, session_id: str, owner: int) -> bool:
        return self.owners.get(session_id) == owner

    def run_turn(self, session_id, items, context):
        self.sent.append((session_id, items, context))
        yield from self.scripts.pop(0)


def read(service: ChatService, who: Viewer, stream_id: str) -> list[tuple[str, dict]]:
    return list(service.events(who, stream_id))


def test_a_read_streams_tokens_and_tools_then_the_answer():
    translator = ChatEvents("ses_1")
    out = [e for raw in READ_THEN_ANSWER for e in translator.feed(raw)] + translator.finish()
    assert [name for name, _ in out] == ["tool_start", "tool_end", "token", "token", "done"]
    assert out[0][1] == {"name": "list_violations"}
    assert out[-1][1] == {"session_id": "ses_1", "reply": "Không có vi phạm."}


def test_sub_agent_threads_are_not_shown():
    translator = ChatEvents("ses_1")
    assert translator.feed({"type": "model.message.delta", "thread_id": "task-1", "content": "x"}) == []


def test_a_failed_turn_is_an_error_and_no_done():
    translator = ChatEvents("ses_1")
    out = translator.feed({"type": "turn.done", "state": {"status": "error", "message": "boom"}}) + translator.finish()
    assert out == [("error", {"message": "boom"})]


def test_the_turn_carries_the_users_token_and_message():
    agent = FakeAgent(READ_THEN_ANSWER)
    service = ChatService(agent)
    started = service.start(viewer(), "tok-1", "  có vi phạm không?  ", None)
    read(service, viewer(), started.stream_id)
    session, items, context = agent.sent[0]
    assert (session, items, context) == (
        "ses_1", [{"type": "user.message", "content": "có vi phạm không?"}], {"Authorization": "Bearer tok-1"},
    )


def test_a_stream_is_readable_once_and_only_by_its_owner():
    service = ChatService(FakeAgent(READ_THEN_ANSWER))
    started = service.start(viewer(1), "t", "hi", None)
    with pytest.raises(NotAllowed):
        service.events(viewer(2), started.stream_id)
    read(service, viewer(1), started.stream_id)
    with pytest.raises(NotAllowed):
        service.events(viewer(1), started.stream_id)


def test_a_conversation_belongs_to_its_user():
    service = ChatService(FakeAgent())
    service.start(viewer(1), "t", "hi", None)
    with pytest.raises(NotAllowed):
        service.start(viewer(2), "t", "hi", "ses_1")


def test_empty_and_huge_messages_are_refused():
    service = ChatService(FakeAgent())
    with pytest.raises(Invalid):
        service.start(viewer(), "t", "   ", None)
    with pytest.raises(Invalid):
        service.start(viewer(), "t", "x" * 9000, None)


def test_without_an_agent_the_chat_is_unavailable():
    with pytest.raises(ServiceUnavailable):
        ChatService(None).start(viewer(), "t", "hi", None)


def test_a_proposal_waits_for_approval_and_is_applied_with_the_users_token():
    agent = FakeAgent(PROPOSE, [
        {"type": "tool.response", "thread_id": "main", "tool_call_id": "c9", "content": "ok"},
        {"type": "model.message", "thread_id": "main", "content": "Đã xóa camera 3.", "tool_calls": []},
    ])
    service = ChatService(agent)
    started = service.start(viewer(), "tok-1", "xóa camera 3", None)
    events = read(service, viewer(), started.stream_id)
    asked = [data for name, data in events if name == "approval_required"]
    assert asked == [{"id": "c9", "summary": "delete_camera(camera_id=3)", "tool": "delete_camera", "args": {"camera_id": 3}}]
    assert events[-1][0] == "done"

    assert service.decide(viewer(), "tok-2", "c9", True) == "Đã xóa camera 3."
    _, items, context = agent.sent[1]
    assert items == [{"type": "user.tool_approval", "thread_id": "main", "tool_call_id": "c9", "approval": {"status": "allow"}}]
    assert context == {"Authorization": "Bearer tok-2"}
    with pytest.raises(NotAllowed):  # answered once
        service.decide(viewer(), "tok-2", "c9", True)


def test_a_proposal_cannot_be_decided_by_someone_else():
    service = ChatService(FakeAgent(PROPOSE))
    started = service.start(viewer(1), "t", "xóa camera 3", None)
    read(service, viewer(1), started.stream_id)
    with pytest.raises(NotAllowed):
        service.decide(viewer(2), "t", "c9", True)


def sse(*events: dict) -> bytes:
    return b"".join(f"id: {i}\ndata: {json.dumps(e)}\n\n".encode() for i, e in enumerate(events))


def test_the_dunly_adapter_speaks_the_api_with_the_key_and_the_context():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path.endswith("/turns"):
            return httpx.Response(200, content=sse(*READ_THEN_ANSWER), headers={"content-type": "text/event-stream"})
        if request.method == "POST":
            return httpx.Response(200, json={"data": {"id": "ses_9"}})
        return httpx.Response(200, json={"data": {"id": "ses_9", "metadata": {"ppe_user": "7"}}})

    chat = DunlyChat("http://dunly:8790/", "sk-dl-key", "ppe-assistant", transport=httpx.MockTransport(handler))
    assert chat.open_session(7) == "ses_9"
    assert json.loads(seen[0].content) == {"agent": {"name": "ppe-assistant"}, "metadata": {"ppe_user": "7"}}
    assert chat.owns_session("ses_9", 7) and not chat.owns_session("ses_9", 8)

    events = list(chat.run_turn("ses_9", [{"type": "user.message", "content": "hi"}], {"Authorization": "Bearer tok"}))
    assert events[-1]["type"] == "turn.done"
    turn = seen[-1]
    assert turn.url.path == "/api/v1/sessions/ses_9/turns"
    assert turn.headers["authorization"] == "Bearer sk-dl-key, Bearer tok"
    assert "context" not in json.loads(turn.content)
    assert json.loads(turn.content)["stream"] is True


def test_a_dunly_error_is_reported_with_its_message():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": {"message": "This API key lacks the sessions:forward scope"}})

    chat = DunlyChat("http://dunly:8790", "k", "a", transport=httpx.MockTransport(handler))
    with pytest.raises(ServiceUnavailable, match="sessions:forward"):
        list(chat.run_turn("s", [], {"Authorization": "Bearer t"}))


# ── what the assistant keeps: pictures, reports, regulations ──────────────────────────────────────────────────

from cloud.application.usecases.chat_files_service import ChatImageService, KnowledgeService, ReportService  # noqa: E402
from cloud.domain.violation.detection import DetectionResult, FoundObject  # noqa: E402
from cloud.domain.policy.regulation import Passage  # noqa: E402
from cloud.infrastructure.files.image_store import FileImageStore  # noqa: E402
from cloud.infrastructure.files.report_store import FileReportStore  # noqa: E402

JPEG = b"\xff\xd8\xff" + b"0" * 20


class FakeDetect:
    def detect(self, image: bytes) -> DetectionResult:
        return DetectionResult((FoundObject("person", 0.9, (0, 0, 1, 1)), FoundObject("no_helmet", 0.8, (0, 0, 1, 1))), JPEG)


def test_a_picture_belongs_to_the_viewer_who_attached_it(tmp_path):
    images = ChatImageService(FileImageStore(tmp_path), FakeDetect())
    image_id = images.attach(viewer(1), JPEG)
    assert images.read(viewer(1), image_id)[1] == "image/jpeg"
    assert images.owns(viewer(1), image_id) and not images.owns(viewer(2), image_id)
    with pytest.raises(NotAllowed):
        images.read(viewer(2), image_id)
    seen = images.look(viewer(1), image_id)
    assert [o.label for o in seen.objects] == ["person", "no_helmet"] and images.owns(viewer(1), seen.annotated_id)


def test_only_pictures_are_accepted(tmp_path):
    images = ChatImageService(FileImageStore(tmp_path), FakeDetect())
    for bad in (b"", b"not a picture", JPEG + b"0" * (9 * 1024 * 1024)):
        with pytest.raises(Invalid):
            images.attach(viewer(), bad)


def test_the_message_tells_the_agent_which_pictures_are_attached(tmp_path):
    images = ChatImageService(FileImageStore(tmp_path), FakeDetect())
    agent = FakeAgent(READ_THEN_ANSWER)
    service = ChatService(agent, images)
    image_id = images.attach(viewer(1), JPEG)
    read(service, viewer(1), service.start(viewer(1), "t", "ảnh này có đội mũ không?", None, [image_id]).stream_id)
    assert agent.sent[0][1][0]["content"].endswith(f"[Ảnh đính kèm: image_id={image_id}]")
    with pytest.raises(NotAllowed):  # someone else's picture
        service.start(viewer(2), "t", "hi", None, [image_id])


def test_a_report_is_a_word_file_with_a_link(tmp_path):
    reports = ReportService(FileReportStore(tmp_path))
    link = reports.export(viewer(), "Báo cáo ngày", "## Tóm tắt\n- 3 vi phạm\n\n| a | b |\n|---|---|\n| 1 | 2 |")
    assert link.startswith("/api/reports/") and link.endswith("/docx")
    assert reports.docx(link.split("/")[3]).startswith(b"PK")
    with pytest.raises(NotAllowed):
        reports.docx("nope")


def test_the_page_is_told_of_a_finished_report():
    translator = ChatEvents("ses_1")
    events = [
        {"type": "model.message", "thread_id": "main", "content": None,
         "tool_calls": [call("c5", "export_safety_report", title="t", body_markdown="b")]},
        {"type": "tool.response", "thread_id": "main", "tool_call_id": "c5", "content": json.dumps({"url": "/api/reports/ab12/docx"})},
    ]
    out = [e for raw in events for e in translator.feed(raw)]
    assert ("report", {"url": "/api/reports/ab12/docx"}) in out
    blocks = [{"type": "text", "text": json.dumps({"url": "/api/reports/cd34/docx"})}]  # how an MCP tool's answer arrives
    again = translator.feed({"type": "tool.response", "thread_id": "main", "tool_call_id": "c5", "content": json.dumps(blocks)})
    assert ("report", {"url": "/api/reports/cd34/docx"}) in again
    other = translator.feed({"type": "tool.response", "thread_id": "main", "tool_call_id": "zz", "content": '{"url": "/x"}'})
    assert other == [("tool_end", {})]


class FakeKnowledge:
    def __init__(self, hits): self.hits = hits
    def has_documents(self): return True
    def search(self, query, top_k=3): return self.hits[:top_k]


def test_regulation_search_cites_its_sources():
    service = KnowledgeService(FakeKnowledge([Passage("tcvn.md", "Điều 5", "Phải đội mũ.", 0.9)]))
    assert service.search("mũ") == "[tcvn.md / Điều 5]\nPhải đội mũ."
    assert KnowledgeService(FakeKnowledge([])).search("x") == "Nothing relevant found in the provided documents."
    with pytest.raises(ServiceUnavailable):
        KnowledgeService(None).search("x")
