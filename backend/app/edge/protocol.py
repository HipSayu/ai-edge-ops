"""The AI Edge Ops server<->edge contract.

Payload models wrapped in ``dqh.svc_core.messaging.Envelope`` + the MQTT-style
topic scheme. This is project-specific and deliberately NOT in svc_core.
"""

from __future__ import annotations

import datetime as dt

from dqh.svc_core.messaging import TopicTemplate
from pydantic import BaseModel, Field

# --- message types (Envelope.type) ------------------------------------------
T_HEARTBEAT = "device.heartbeat"
T_TELEMETRY = "device.telemetry"
T_STATE_REPORT = "device.state"
T_VIOLATION = "device.violation"
T_DEPLOY_MODEL = "command.deploy_model"
T_UPDATE_CONFIG = "command.update_config"
T_COMMAND_ACK = "command.ack"

# --- topics (namespace: "fleet") ------------------------------------------
NS = "fleet"
TOPIC_STATE = TopicTemplate(f"{NS}/devices/{{device_id}}/state")
TOPIC_TELEMETRY = TopicTemplate(f"{NS}/devices/{{device_id}}/telemetry")
TOPIC_EVENTS = TopicTemplate(f"{NS}/devices/{{device_id}}/events")
TOPIC_CMD = TopicTemplate(f"{NS}/devices/{{device_id}}/cmd")
TOPIC_ACK = TopicTemplate(f"{NS}/devices/{{device_id}}/ack")

# wildcards the gateway subscribes to
SUB_STATE = f"{NS}/devices/+/state"
SUB_TELEMETRY = f"{NS}/devices/+/telemetry"
SUB_EVENTS = f"{NS}/devices/+/events"
SUB_ACK = f"{NS}/devices/+/ack"


# --- edge -> server payloads ------------------------------------------------
class HeartbeatPayload(BaseModel):
    cpu_percent: float | None = None
    gpu_percent: float | None = None
    mem_percent: float | None = None
    temperature_c: float | None = None
    fps: float | None = None
    inference_latency_ms: float | None = None
    active_model_version_id: int | None = None
    recorded_at: dt.datetime | None = None


class ViolationPayload(BaseModel):
    zone: str
    violation_type: str
    confidence: float
    image_path: str | None = None
    recorded_at: dt.datetime | None = None


class StateReportPayload(BaseModel):
    active_model_version_id: int | None = None
    deployment_id: int | None = None
    runtime_status: str = "unknown"          # applying | active | failed
    config: dict = Field(default_factory=dict)
    detail: str | None = None


# --- server -> edge payloads ----------------------------------------------
class DeployModelPayload(BaseModel):
    deployment_id: int
    model_version_id: int
    artifact_uri: str
    format: str
    config: dict = Field(default_factory=dict)


class UpdateConfigPayload(BaseModel):
    deployment_id: int
    config: dict


class CommandAckPayload(BaseModel):
    command_id: str
    deployment_id: int | None = None
    status: str                              # accepted | in_progress | succeeded | failed
    detail: str | None = None


__all__ = [
    "T_HEARTBEAT",
    "T_TELEMETRY",
    "T_STATE_REPORT",
    "T_VIOLATION",
    "T_DEPLOY_MODEL",
    "T_UPDATE_CONFIG",
    "T_COMMAND_ACK",
    "NS",
    "TOPIC_STATE",
    "TOPIC_TELEMETRY",
    "TOPIC_EVENTS",
    "TOPIC_CMD",
    "TOPIC_ACK",
    "SUB_STATE",
    "SUB_TELEMETRY",
    "SUB_EVENTS",
    "SUB_ACK",
    "HeartbeatPayload",
    "ViolationPayload",
    "StateReportPayload",
    "DeployModelPayload",
    "UpdateConfigPayload",
    "CommandAckPayload",
]
