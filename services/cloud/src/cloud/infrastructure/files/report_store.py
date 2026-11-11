from pathlib import Path

from cloud.infrastructure.files.docx_report import save_report


class FileReportStore:
    """The ReportStore port: one docx file per report."""

    def __init__(self, folder: Path) -> None:
        self._folder = folder

    def save(self, title: str, body_markdown: str, author: str) -> str:
        return save_report(self._folder, title, body_markdown, author)

    def read_docx(self, report_id: str) -> bytes | None:
        if not report_id.isalnum():  # ids are hex; anything else could be a path trick
            return None
        path = self._folder / f"{report_id}.docx"
        return path.read_bytes() if path.is_file() else None
