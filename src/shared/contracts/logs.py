"""Runtime log shipping: `edge/{cluster}/{node}/logs/{runtime_id}` carries a batch of new container log lines."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.shared.contracts.enums import Severity


class RuntimeLogLine(BaseModel):
    timestamp: datetime
    level: Severity = Severity.INFO
    message: str


class RuntimeLogBatch(BaseModel):
    node_id: str
    runtime_id: str
    runtime_name: str
    lines: list[RuntimeLogLine] = Field(default_factory=list)
