from __future__ import annotations

import asyncio
import json
import logging
import posixpath
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager

from hopquangdo.containers import ContainerEngine, ContainerError, ContainerNotFound, ContainerState

from src.edge.application.ports.artifact_fetcher import ArtifactFetcher
from src.edge.application.services.runtime_containers import RuntimeContainers
from src.edge.domain.entities.runtime_instance import RuntimeInstance
from src.shared.contracts import RuntimeSpec, RuntimeState, RuntimeStatus
from src.shared.exceptions import AppException, ErrorCode

logger = logging.getLogger(__name__)

StatusListener = Callable[[RuntimeInstance, RuntimeStatus], Awaitable[None]]

MODEL_MOUNT_DIR = "/models"


@contextmanager
def _engine_errors() -> Iterator[None]:
    """Container engine errors as AppException, so every caller reports them the same way."""
    try:
        yield
    except ContainerNotFound as exc:
        raise AppException(ErrorCode.NOT_FOUND, str(exc)) from exc
    except ContainerError as exc:
        raise AppException(ErrorCode.EXTERNAL_SERVICE, str(exc)) from exc


class RuntimeService:
    """Owns the node's desired runtimes and reconciles them against the container engine.

    Each runtime has its own lock, so a slow image pull for one runtime never blocks the others.
    """

    def __init__(
        self,
        engine: ContainerEngine,
        containers: RuntimeContainers,
        fetcher: ArtifactFetcher,
        base_env: dict[str, str] | None = None,
    ) -> None:
        self._engine = engine
        self._containers = containers
        self._fetcher = fetcher
        self._base_env = base_env or {}
        self._instances: dict[str, RuntimeInstance] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._listeners: list[StatusListener] = []

    def on_status_change(self, listener: StatusListener) -> None:
        self._listeners.append(listener)

    def list(self) -> list[RuntimeInstance]:
        return list(self._instances.values())

    def get(self, runtime_id: str) -> RuntimeInstance:
        instance = self._instances.get(runtime_id)
        if instance is None:
            raise AppException(ErrorCode.NOT_FOUND, f"Runtime {runtime_id} not found on node")
        return instance

    def snapshot(self) -> list[RuntimeState]:
        return [i.to_state() for i in self._instances.values()]

    def _lock(self, runtime_id: str) -> asyncio.Lock:
        return self._locks.setdefault(runtime_id, asyncio.Lock())

    async def restore(self) -> None:
        """Takes over this node's containers already in the engine (the engine is the source of truth
        after a restart). A node without a reachable engine starts empty instead of failing: it still
        reports to the Cloud.
        """
        try:
            containers = await self._engine.list(self._containers.owned())
        except ContainerError as exc:
            logger.warning("No runtimes restored, container engine unavailable: %s", exc)
            return
        managed = [m for m in map(self._containers.to_managed, containers) if m is not None]
        for m in managed:
            self._instances[m.spec.runtime_id] = RuntimeInstance(
                spec=m.spec, desired_running=m.desired_running, container_id=m.container_id,
                status=RuntimeStatus.RUNNING if m.desired_running else RuntimeStatus.STOPPED,
            )
        logger.info("Restored %d runtime(s) from the container engine", len(managed))
        await self.reconcile()

    async def apply(self, spec: RuntimeSpec) -> RuntimeInstance:
        async with self._lock(spec.runtime_id):
            instance = self._instances.get(spec.runtime_id)
            if instance is None:
                instance = self._instances[spec.runtime_id] = RuntimeInstance(spec=spec)
            elif instance.spec == spec and instance.status == RuntimeStatus.RUNNING:
                return instance  # re-sent deploy: already in the desired state, keep the container
            instance.spec = spec
            await self._launch(instance)
            return instance

    async def start(self, runtime_id: str) -> RuntimeInstance:
        async with self._lock(runtime_id):
            instance = self.get(runtime_id)
            instance.desired_running = True
            await self._set_status(instance, RuntimeStatus.STARTING)
            if not await self._on_container(instance, self._engine.start):
                await self._launch(instance)
            await self._set_status(instance, RuntimeStatus.RUNNING)
            return instance

    async def stop(self, runtime_id: str) -> RuntimeInstance:
        async with self._lock(runtime_id):
            instance = self.get(runtime_id)
            instance.desired_running = False
            await self._set_status(instance, RuntimeStatus.STOPPING)
            await self._on_container(instance, self._engine.stop)
            await self._set_status(instance, RuntimeStatus.STOPPED)
            return instance

    async def restart(self, runtime_id: str) -> RuntimeInstance:
        async with self._lock(runtime_id):
            instance = self.get(runtime_id)
            instance.desired_running = True
            await self._set_status(instance, RuntimeStatus.RESTARTING)
            if not await self._on_container(instance, self._engine.restart):
                await self._launch(instance)
            await self._set_status(instance, RuntimeStatus.RUNNING)
            return instance

    async def remove(self, runtime_id: str) -> None:
        async with self._lock(runtime_id):
            instance = self._instances.get(runtime_id)
            if instance is None:
                return
            await self._set_status(instance, RuntimeStatus.STOPPING)
            await self._on_container(instance, self._engine.remove)
            del self._instances[runtime_id]
            self._locks.pop(runtime_id, None)
            await self._set_status(instance, RuntimeStatus.STOPPED)

    async def reconcile(self) -> None:
        """Syncs each runtime's status with its container, and relaunches containers that disappeared
        (e.g. removed by hand) while still desired. The engine restarts crashed containers itself.
        """
        for instance in self.list():
            async with self._lock(instance.runtime_id):
                if instance.runtime_id not in self._instances:
                    continue  # removed while waiting for the lock
                try:
                    state = await self._engine.inspect(instance.container_id) if instance.container_id else None
                except ContainerError as exc:
                    logger.warning("Reconcile skipped, container engine unavailable: %s", exc)
                    return
                if state is None and instance.desired_running:
                    logger.warning("Container of runtime %s is gone, relaunching", instance.runtime_id)
                    try:
                        await self._launch(instance)
                    except AppException:
                        pass  # logged and marked FAILED by _launch; retried next reconcile
                    continue
                await self._observe(instance, state)

    async def _observe(self, instance: RuntimeInstance, state: ContainerState | None) -> None:
        if state is None:
            instance.container_id = None
            await self._set_status(instance, RuntimeStatus.STOPPED)
            return
        instance.restart_count = state.restart_count
        instance.started_at = state.started_at or instance.started_at
        if state.running:
            instance.message = None
            await self._set_status(instance, RuntimeStatus.RUNNING)
        elif not instance.desired_running:
            await self._set_status(instance, RuntimeStatus.STOPPED)
        else:
            instance.message = state.error or f"exited with code {state.exit_code}"
            crash_looping = state.status == "restarting"
            await self._set_status(instance, RuntimeStatus.RESTARTING if crash_looping else RuntimeStatus.FAILED)

    async def _on_container(self, instance: RuntimeInstance, action: Callable[[str], Awaitable[None]]) -> bool:
        """Runs `action` on the runtime's container; False when there is no container (anymore).
        Any other failure marks the runtime FAILED and is raised as AppException.
        """
        if not instance.container_id:
            return False
        try:
            with _engine_errors():
                await action(instance.container_id)
            return True
        except AppException as exc:
            if exc.code == ErrorCode.NOT_FOUND:
                instance.container_id = None
                return False
            await self._fail(instance, exc)
            raise

    async def _launch(self, instance: RuntimeInstance) -> None:
        spec = instance.spec
        try:
            await self._set_status(instance, RuntimeStatus.CREATING)
            env = {**self._base_env, **spec.environment,
                   "RUNTIME_ID": spec.runtime_id, "RUNTIME_NAME": spec.name, "RUNTIME_CONFIG": json.dumps(spec.config)}
            mounts: dict[str, str] = {}
            if spec.model_uri:
                host_path = await self._fetcher.fetch(spec.model_uri)
                container_path = posixpath.join(MODEL_MOUNT_DIR, posixpath.basename(host_path.replace("\\", "/")))
                mounts[host_path] = container_path
                env["MODEL_PATH"] = container_path
            with _engine_errors():
                await self._engine.pull(spec.image)
                await self._set_status(instance, RuntimeStatus.STARTING)
                container = await self._engine.run(self._containers.to_container(spec, env, mounts))
            instance.container_id = container.name
            instance.started_at = container.started_at
            instance.message = None
            instance.desired_running = True
            await self._set_status(instance, RuntimeStatus.RUNNING)
        except AppException as exc:
            await self._fail(instance, exc)
            raise
        except Exception as exc:
            await self._fail(instance, exc)
            raise AppException(ErrorCode.EXTERNAL_SERVICE, f"Launch failed: {exc}") from exc

    async def _fail(self, instance: RuntimeInstance, exc: Exception) -> None:
        instance.message = exc.message if isinstance(exc, AppException) else str(exc)
        logger.error("Runtime %s failed: %s", instance.runtime_id, instance.message)
        await self._set_status(instance, RuntimeStatus.FAILED)

    async def _set_status(self, instance: RuntimeInstance, status: RuntimeStatus) -> None:
        if instance.status == status:
            return
        instance.status = status
        for listener in self._listeners:
            try:
                await listener(instance, status)
            except Exception:
                logger.exception("Status listener failed")
