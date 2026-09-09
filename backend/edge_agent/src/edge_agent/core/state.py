"""Local desired-vs-reported state, persisted to a JSON file."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class DesiredState:
    deployment_id: int | None = None
    model_version_id: int | None = None
    image: str | None = None  # digest-pinned OCI ref the inference service runs
    config: dict = field(default_factory=dict)


@dataclass
class ReportedState:
    deployment_id: int | None = None
    active_model_version_id: int | None = None
    runtime_status: str = "idle"          # idle | applying | active | failed
    detail: str | None = None
    config: dict = field(default_factory=dict)


@dataclass
class AgentState:
    desired: DesiredState = field(default_factory=DesiredState)
    reported: ReportedState = field(default_factory=ReportedState)

    def in_sync(self) -> bool:
        return (
            self.desired.model_version_id == self.reported.active_model_version_id
            and self.reported.runtime_status == "active"
        )


class StateStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.state = self._load()

    def _load(self) -> AgentState:
        if not self.path.exists():
            return AgentState()
        raw = json.loads(self.path.read_text())
        return AgentState(
            desired=DesiredState(**raw.get("desired", {})),
            reported=ReportedState(**raw.get("reported", {})),
        )

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {"desired": asdict(self.state.desired), "reported": asdict(self.state.reported)},
                indent=2,
            )
        )
