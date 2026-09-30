from fastapi import APIRouter, Depends, status

from apps.edge.api.schemas import AcceptedOut, RuntimeEventIn
from apps.edge.dependencies import get_runtime_service, get_telemetry_report_service
from src.edge.application.services.reporting import TelemetryReportService
from src.edge.application.services.runtime_service import RuntimeService
from src.shared.contracts import RuntimeTelemetry

# Runtime -> Agent reporting; the agent relays to the Cloud over MQTT.
router = APIRouter(prefix="/runtimes/{runtime_id}", tags=["reporting"])


@router.post("/telemetry", response_model=AcceptedOut, status_code=status.HTTP_202_ACCEPTED)
async def runtime_telemetry(
    runtime_id: str,
    sample: RuntimeTelemetry,
    runtimes: RuntimeService = Depends(get_runtime_service),
    reporter: TelemetryReportService = Depends(get_telemetry_report_service),
):
    runtimes.get(runtime_id)
    await reporter.relay_runtime_telemetry(runtime_id, sample)
    return AcceptedOut()


@router.post("/events", response_model=AcceptedOut, status_code=status.HTTP_202_ACCEPTED)
async def runtime_event(
    runtime_id: str,
    body: RuntimeEventIn,
    runtimes: RuntimeService = Depends(get_runtime_service),
    reporter: TelemetryReportService = Depends(get_telemetry_report_service),
):
    runtimes.get(runtime_id)
    await reporter.relay_runtime_event(runtime_id, body.event_type, body.message, body.severity, body.data)
    return AcceptedOut()
