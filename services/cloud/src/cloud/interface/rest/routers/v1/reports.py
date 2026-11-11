"""Reports the assistant wrote, as Word files."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from cloud.interface.rest.deps import current_user, get_container
from cloud.bootstrap.container import Container
from shared.viewer import Viewer

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{report_id}/docx")
def report_docx(report_id: str, viewer: Viewer = Depends(current_user), container: Container = Depends(get_container)):
    """Downloads a report. The page fetches it with the Authorization header and saves the answer."""
    return Response(
        container.reports.docx(report_id),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="bao-cao-{report_id}.docx"'},
    )
