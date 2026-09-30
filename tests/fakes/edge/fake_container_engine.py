from datetime import datetime

from hopquangdo.containers import ContainerNotFound, ContainerSpec, ContainerState, EngineUnavailable, LogLine


class FakeContainerEngine:
    """ContainerEngine keeping containers in memory. `crash()` / `vanish()` simulate what happens outside the agent."""

    def __init__(self, reachable: bool = True) -> None:
        self.reachable = reachable
        self.containers: dict[str, ContainerState] = {}
        self.pulled: list[str] = []

    def _check(self) -> None:
        if not self.reachable:
            raise EngineUnavailable("fake engine down")

    def _get(self, name: str) -> ContainerState:
        self._check()
        if name not in self.containers:
            raise ContainerNotFound(name)
        return self.containers[name]

    def _set(self, name: str, **changes) -> None:
        old = self.containers[name]
        self.containers[name] = ContainerState(**{**{f: getattr(old, f) for f in old.__slots__}, **changes})

    async def pull(self, image: str) -> None:
        self._check()
        self.pulled.append(image)

    async def run(self, spec: ContainerSpec) -> ContainerState:
        self._check()
        state = ContainerState(id=spec.name, name=spec.name, image=spec.image, labels=dict(spec.labels),
                               running=True, status="running")
        self.containers[spec.name] = state
        return state

    async def start(self, container: str) -> None:
        self._get(container)
        self._set(container, running=True, status="running", exit_code=None)

    async def stop(self, container: str, timeout_sec: int = 10) -> None:
        if container in self.containers:
            self._set(container, running=False, status="exited", exit_code=0)

    async def restart(self, container: str, timeout_sec: int = 10) -> None:
        old = self._get(container)
        self._set(container, running=True, status="running", exit_code=None, restart_count=old.restart_count + 1)

    async def remove(self, container: str) -> None:
        self._check()
        self.containers.pop(container, None)

    async def inspect(self, container: str) -> ContainerState | None:
        self._check()
        return self.containers.get(container)

    async def logs(self, container: str, since: datetime | None = None, limit: int = 200) -> list[LogLine]:
        self._get(container)
        return []

    async def list(self, labels: dict[str, str | None] | None = None) -> list[ContainerState]:
        self._check()
        return [c for c in self.containers.values()
                if all(k in c.labels and (v is None or c.labels[k] == v) for k, v in (labels or {}).items())]

    # --- simulated outside events ---
    def crash(self, container: str, exit_code: int = 1, restarting: bool = False) -> None:
        self._set(container, running=False, status="restarting" if restarting else "exited", exit_code=exit_code)

    def vanish(self, container: str) -> None:
        self.containers.pop(container)
