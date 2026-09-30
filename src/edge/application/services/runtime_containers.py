import logging
import re
from dataclasses import dataclass

from hopquangdo.containers import ContainerSpec, ContainerState, LogLine

from src.shared.contracts import RuntimeLogLine, RuntimeSpec, Severity

logger = logging.getLogger(__name__)

RUNTIME_LABEL = "edgeops.runtime_id"
# Node that owns the container: several agents (demo sims) may share one engine
NODE_LABEL = "edgeops.node_id"
# Full RuntimeSpec as JSON, so a restarted agent can take its containers over again
SPEC_LABEL = "edgeops.runtime_spec"
_NAME = re.compile(r"^edgeops-(?P<name>.+)-[0-9a-f]{8}$")
_ERROR_WORDS = ("ERROR", "CRIT", "FATAL", "EMERG", "TRACEBACK")


@dataclass(frozen=True)
class ManagedRuntime:
    """A runtime found in the container engine, so an agent restart can take it over again."""

    spec: RuntimeSpec
    container_id: str
    desired_running: bool


class RuntimeContainers:
    """Maps this node's runtimes to engine containers and back (names, labels, limits, log levels)."""

    def __init__(self, node_id: str) -> None:
        self._node_id = node_id

    def owned(self) -> dict[str, str | None]:
        """Label selector for every runtime container of this node."""
        return {RUNTIME_LABEL: None, NODE_LABEL: self._node_id}

    def to_container(self, spec: RuntimeSpec, env: dict[str, str], mounts: dict[str, str]) -> ContainerSpec:
        limits = spec.resource_limits
        return ContainerSpec(
            name=f"edgeops-{re.sub(r'[^a-zA-Z0-9_.-]', '-', spec.name).lower()}-{spec.runtime_id[:8].lower()}",
            image=spec.image,
            env={k: str(v) for k, v in env.items()},
            mounts=mounts,
            labels={RUNTIME_LABEL: spec.runtime_id, NODE_LABEL: self._node_id, SPEC_LABEL: spec.model_dump_json()},
            cpus=limits.get("cpus"),
            memory=limits.get("memory"),
            gpus=limits.get("gpus"),
            # Runtimes call back to the agent's local API on the host
            extra_hosts={"host.docker.internal": "host-gateway"},
        )

    @staticmethod
    def to_managed(container: ContainerState) -> ManagedRuntime | None:
        labels = container.labels
        try:
            if raw := labels.get(SPEC_LABEL):
                spec = RuntimeSpec.model_validate_json(raw)
            else:
                # No spec label: rebuild what the container itself records
                image = container.image
                uri, _, tag = image.rpartition(":") if ":" in image.rsplit("/", 1)[-1] else (image, "", "latest")
                match = _NAME.match(container.name)
                spec = RuntimeSpec(runtime_id=labels[RUNTIME_LABEL], name=match["name"] if match else container.name,
                                   image_uri=uri, image_tag=tag or "latest")
        except Exception as exc:  # malformed label or foreign container: leave it alone
            logger.warning("Cannot adopt container %s: %s", container.name, exc)
            return None
        return ManagedRuntime(spec=spec, container_id=container.name,
                              desired_running=container.running or container.status == "restarting")

    @staticmethod
    def to_log_line(line: LogLine) -> RuntimeLogLine:
        upper = line.message.upper()
        level = (Severity.ERROR if any(w in upper for w in _ERROR_WORDS)
                 else Severity.WARNING if "WARN" in upper else Severity.INFO)
        return RuntimeLogLine(timestamp=line.timestamp, level=level, message=line.message)
