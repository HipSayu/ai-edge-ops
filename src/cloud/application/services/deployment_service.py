from __future__ import annotations

import uuid

from src.cloud.application.dto.deployment_request import DeploymentRequest
from src.cloud.application.dto.deployment_update import DeploymentUpdate
from src.cloud.application.ports.command_publisher import CommandPublisher
from src.cloud.application.ports.deployment_repository import DeploymentRepository
from src.cloud.application.ports.node_repository import NodeRepository
from src.cloud.application.ports.runtime_repository import RuntimeRepository
from src.cloud.domain.entities.deployment import Deployment
from src.cloud.domain.entities.runtime import Runtime
from src.shared.contracts import Command, CommandType, DeploymentStatus, RuntimeRef, RuntimeSpec, RuntimeStatus
from src.shared.exceptions import AppException, ErrorCode

_LIFECYCLE = {CommandType.START, CommandType.STOP, CommandType.RESTART}


class DeploymentService:
    """Records desired state and dispatches commands; the edge reports results asynchronously."""

    def __init__(
        self,
        deployments: DeploymentRepository,
        nodes: NodeRepository,
        runtimes: RuntimeRepository,
        publisher: CommandPublisher,
    ) -> None:
        self._deployments = deployments
        self._nodes = nodes
        self._runtimes = runtimes
        self._publisher = publisher

    async def create(self, request: DeploymentRequest) -> Deployment:
        node = await self._nodes.get(request.node_id)
        if node is None:
            raise AppException(ErrorCode.NOT_FOUND, f"Node {request.node_id} not found")

        existing = next((r for r in await self._runtimes.list(node.id) if r.name == request.name), None)
        if existing is not None:
            deployment = await self._deployments.get_by_runtime(existing.id)
            if deployment is not None and not deployment.is_removed():
                spec = self._spec(existing.id, request)
                if deployment.runtime_spec() == spec:
                    return deployment  # idempotent re-submit
                raise AppException(
                    ErrorCode.CONFLICT,
                    f"Runtime '{request.name}' already deployed on node {node.id}; use PUT to update",
                    {"deployment_id": deployment.id},
                )

        runtime_id = str(uuid.uuid4())
        spec = self._spec(runtime_id, request)
        await self._runtimes.add(
            Runtime(
                id=runtime_id, node_id=node.id, name=spec.name, type=spec.type, status=RuntimeStatus.CREATING,
                image_uri=spec.image_uri, image_tag=spec.image_tag, model_id=spec.model_id,
                config=spec.config, environment=spec.environment, resource_limits=spec.resource_limits,
            )
        )
        deployment = await self._deployments.add(
            Deployment(
                id=str(uuid.uuid4()), cluster_id=node.cluster_id, node_id=node.id,
                runtime_id=runtime_id, spec=spec.model_dump(mode="json"),
            )
        )
        await self._dispatch(deployment, Command(type=CommandType.DEPLOY, deployment_id=deployment.id, runtime=spec))
        return deployment

    async def update(self, deployment_id: str, patch: DeploymentUpdate) -> Deployment:
        deployment = await self._require_active(deployment_id)
        changes = patch.model_dump(exclude_none=True)
        if not changes:
            raise AppException(ErrorCode.INVALID_REQUEST, "No fields to update")
        spec = deployment.runtime_spec().model_copy(update=changes)
        deployment.spec = spec.model_dump(mode="json")

        runtime = await self._runtimes.get(deployment.runtime_id)
        if runtime is not None:
            runtime.image_uri, runtime.image_tag, runtime.model_id = spec.image_uri, spec.image_tag, spec.model_id
            runtime.config, runtime.environment = spec.config, spec.environment
            runtime.resource_limits = spec.resource_limits
            await self._runtimes.save(runtime)

        await self._dispatch(deployment, Command(type=CommandType.UPDATE, deployment_id=deployment.id, runtime=spec))
        return deployment

    async def remove(self, deployment_id: str) -> Deployment:
        deployment = await self._require_active(deployment_id)
        command = Command(
            type=CommandType.REMOVE, deployment_id=deployment.id, target=RuntimeRef(runtime_id=deployment.runtime_id)
        )
        await self._dispatch(deployment, command, DeploymentStatus.REMOVING)
        return deployment

    async def control_runtime(self, runtime_id: str, action: CommandType) -> Deployment:
        if action not in _LIFECYCLE:
            raise AppException(ErrorCode.INVALID_REQUEST, f"Unsupported runtime action: {action}")
        deployment = await self._deployments.get_by_runtime(runtime_id)
        if deployment is None or deployment.is_removed():
            raise AppException(ErrorCode.NOT_FOUND, f"No active deployment for runtime {runtime_id}")
        command = Command(type=action, deployment_id=deployment.id, target=RuntimeRef(runtime_id=runtime_id))
        await self._dispatch(deployment, command)
        return deployment

    async def get(self, deployment_id: str) -> Deployment:
        deployment = await self._deployments.get(deployment_id)
        if deployment is None:
            raise AppException(ErrorCode.NOT_FOUND, f"Deployment {deployment_id} not found")
        return deployment

    async def list(self, node_id: str | None = None) -> list[Deployment]:
        return await self._deployments.list(node_id)

    async def _require_active(self, deployment_id: str) -> Deployment:
        deployment = await self.get(deployment_id)
        if deployment.is_removed():
            raise AppException(ErrorCode.CONFLICT, f"Deployment {deployment_id} is removed")
        return deployment

    async def _dispatch(
        self, deployment: Deployment, command: Command, status: DeploymentStatus = DeploymentStatus.IN_PROGRESS
    ) -> None:
        deployment.dispatched(command.command_id, status)
        await self._deployments.save(deployment)
        await self._publisher.send(deployment.cluster_id, deployment.node_id, command)

    @staticmethod
    def _spec(runtime_id: str, request: DeploymentRequest) -> RuntimeSpec:
        return RuntimeSpec(runtime_id=runtime_id, **request.model_dump(exclude={"node_id"}))
