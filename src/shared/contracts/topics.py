from dataclasses import dataclass

from src.shared.contracts.commands import CommandType


@dataclass(frozen=True, slots=True)
class TopicAddress:
    """A parsed `edge/{cluster_id}/{node_id}/{channel}[/{kind}]` topic."""

    cluster_id: str
    node_id: str
    channel: str
    kind: str | None


class EdgeTopics:
    """MQTT topic builder/parser following docs/api/Readme.md §5."""

    ROOT = "edge"
    COMMAND = "command"
    STATE = "state"
    TELEMETRY = "telemetry"
    EVENT = "event"
    LOGS = "logs"

    def __init__(self, cluster_id: str, node_id: str) -> None:
        self.cluster_id = cluster_id
        self.node_id = node_id
        self._base = f"{self.ROOT}/{cluster_id}/{node_id}"

    # --- commands (Cloud -> Edge) ---
    def command(self, command_type: CommandType) -> str:
        return f"{self._base}/{self.COMMAND}/{command_type.value}"

    def commands(self) -> str:
        return f"{self._base}/{self.COMMAND}/+"

    # --- state (Edge -> Cloud, retained) ---
    def state(self) -> str:
        return f"{self._base}/{self.STATE}"

    def runtime_state(self) -> str:
        return f"{self._base}/{self.STATE}/runtime"

    # --- telemetry (Edge -> Cloud) ---
    def telemetry(self, kind: str) -> str:
        return f"{self._base}/{self.TELEMETRY}/{kind}"

    # --- events (Edge -> Cloud) ---
    def event(self, kind: str) -> str:
        return f"{self._base}/{self.EVENT}/{kind}"

    # --- runtime container logs (Edge -> Cloud) ---
    def logs(self, runtime_id: str) -> str:
        return f"{self._base}/{self.LOGS}/{runtime_id}"

    # --- fleet-wide wildcards (Cloud subscriptions) ---
    @classmethod
    def all_logs(cls) -> str:
        return f"{cls.ROOT}/+/+/{cls.LOGS}/+"

    @classmethod
    def all_states(cls) -> str:
        return f"{cls.ROOT}/+/+/{cls.STATE}/#"

    @classmethod
    def all_telemetry(cls) -> str:
        return f"{cls.ROOT}/+/+/{cls.TELEMETRY}/+"

    @classmethod
    def all_events(cls) -> str:
        return f"{cls.ROOT}/+/+/{cls.EVENT}/+"

    @classmethod
    def parse(cls, topic: str) -> TopicAddress:
        parts = topic.split("/")
        if len(parts) < 4 or parts[0] != cls.ROOT:
            raise ValueError(f"Not an edge topic: {topic}")
        return TopicAddress(
            cluster_id=parts[1],
            node_id=parts[2],
            channel=parts[3],
            kind="/".join(parts[4:]) or None,
        )


class TelemetryKind:
    SYSTEM = "system"
    RUNTIME = "runtime"
    GPU = "gpu"
    HEALTH = "health"


class EventKind:
    RUNTIME = "runtime"
    ERROR = "error"
    DEPLOYMENT = "deployment"
    HEALTH = "health"
