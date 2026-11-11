"""What the chat keeps for the assistant: pictures users attach, the reports it writes, and the regulation documents."""

from dataclasses import dataclass

from cloud.application.ports import ImageStore, KnowledgeBase, ReportStore
from cloud.domain.violation.detection import FoundObject
from shared.errors import Invalid, ServiceUnavailable
from shared.text import found
from shared.viewer import Viewer

_SIGNATURES = ((b"\xff\xd8\xff", "jpg"), (b"\x89PNG\r\n\x1a\n", "png"))
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MEDIA_TYPE = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
REPORT_URL_PREFIX = "/api/reports/"
IMAGE_URL_PREFIX = "/api/chat/images/"


def report_url(report_id: str) -> str:
    return f"{REPORT_URL_PREFIX}{report_id}/docx"


def _extension_of(data: bytes) -> str | None:
    for signature, extension in _SIGNATURES:
        if data.startswith(signature):
            return extension
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


@dataclass(frozen=True)
class Seen:
    """What the detector saw in one attached picture."""

    objects: tuple[FoundObject, ...]
    annotated_id: str  # the picture with the boxes drawn, kept as a chat picture too


class ChatImageService:
    """Pictures of a chat: attaching one, and having the PPE model look at one. Each belongs to one viewer."""

    def __init__(self, store: ImageStore, detect) -> None:
        self._store = store
        self._detect = detect  # DetectService

    def attach(self, viewer: Viewer, data: bytes) -> str:
        if not data:
            raise Invalid("Ảnh trống")
        if len(data) > MAX_IMAGE_BYTES:
            raise Invalid(f"Ảnh quá lớn (tối đa {MAX_IMAGE_BYTES // 1024 // 1024} MB)")
        extension = _extension_of(data)
        if extension is None:
            raise Invalid("Chỉ nhận ảnh JPEG, PNG hoặc WebP")
        return self._store.save(viewer.id, data, extension)

    def read(self, viewer: Viewer, image_id: str) -> tuple[bytes, str]:
        """(content, media type)."""
        content, extension = found(self._store.read(viewer.id, image_id), "Không tìm thấy ảnh")
        return content, MEDIA_TYPE[extension]

    def owns(self, viewer: Viewer, image_id: str) -> bool:
        return self._store.read(viewer.id, image_id) is not None

    def look(self, viewer: Viewer, image_id: str) -> Seen:
        """Runs the PPE model on an attached picture."""
        content, _ = found(self._store.read(viewer.id, image_id), "Không tìm thấy ảnh")
        result = self._detect.detect(content)
        return Seen(result.objects, self._store.save(viewer.id, result.annotated_jpeg, "jpg"))


class ReportService:
    def __init__(self, store: ReportStore) -> None:
        self._store = store

    def export(self, viewer: Viewer, title: str, body_markdown: str) -> str:
        """Saves a finished report as a Word file; returns the link to download it."""
        return report_url(self._store.save(title, body_markdown, viewer.full_name))

    def docx(self, report_id: str) -> bytes:
        return found(self._store.read_docx(report_id), "Không tìm thấy báo cáo")


class KnowledgeService:
    def __init__(self, knowledge: KnowledgeBase | None) -> None:
        self._knowledge = knowledge

    def search(self, query: str, top_k: int = 3) -> str:
        if self._knowledge is None:
            raise ServiceUnavailable("Chưa cấu hình kho quy định (CLOUD_QDRANT_URL, CLOUD_EMBEDDING_BASE_URL)")
        if not self._knowledge.has_documents():
            return "The knowledge base is empty: no documents have been provided yet."
        hits = self._knowledge.search(query, max(1, min(top_k, 10)))
        if not hits:
            return "Nothing relevant found in the provided documents."
        return "\n\n".join(f"[{h.source} / {h.heading}]\n{h.text[:1200]}" for h in hits)
