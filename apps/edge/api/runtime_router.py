from fastapi import APIRouter, Depends, status

from apps.edge.api.schemas import CommandResultOut
from apps.edge.dependencies import get_command_service, get_runtime_service
from src.edge.application.services.command_service import CommandService
from src.edge.application.services.runtime_service import RuntimeService
from src.shared.contracts import CommandType, RuntimeSpec, RuntimeState

# Mutations go through the same CommandService as MQTT commands, so results are reported to the Cloud.
router = APIRouter(prefix="/runtimes", tags=["runtimes"])


@router.get("", response_model=list[RuntimeState])
async def list_runtimes(service: RuntimeService = Depends(get_runtime_service)):
    return service.snapshot()


@router.get("/{runtime_id}", response_model=RuntimeState)
async def get_runtime(runtime_id: str, service: RuntimeService = Depends(get_runtime_service)):
    return service.get(runtime_id).to_state()


@router.post("", response_model=CommandResultOut, status_code=status.HTTP_201_CREATED)
async def create_runtime(spec: RuntimeSpec, service: CommandService = Depends(get_command_service)):
    return await service.deploy(spec)


@router.put("/{runtime_id}", response_model=CommandResultOut)
async def update_runtime(
    runtime_id: str, spec: RuntimeSpec, service: CommandService = Depends(get_command_service)
):
    return await service.update(runtime_id, spec)


@router.delete("/{runtime_id}", response_model=CommandResultOut)
async def delete_runtime(runtime_id: str, service: CommandService = Depends(get_command_service)):
    return await service.remove(runtime_id)


@router.post("/{runtime_id}/start", response_model=CommandResultOut)
async def start_runtime(runtime_id: str, service: CommandService = Depends(get_command_service)):
    return await service.control(runtime_id, CommandType.START)


@router.post("/{runtime_id}/stop", response_model=CommandResultOut)
async def stop_runtime(runtime_id: str, service: CommandService = Depends(get_command_service)):
    return await service.control(runtime_id, CommandType.STOP)


@router.post("/{runtime_id}/restart", response_model=CommandResultOut)
async def restart_runtime(runtime_id: str, service: CommandService = Depends(get_command_service)):
    return await service.control(runtime_id, CommandType.RESTART)
