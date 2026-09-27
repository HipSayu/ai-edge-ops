"""AI Edge Ops server<->edge contract — shared by ``server`` and ``edge_agent``.

Payloads travel as ``dqh.svc_core.contracts.messaging.Envelope[<Payload>]``; ``Envelope.type``
is one of the ``T_*`` constants; topics follow the ``agent/devices/{id}/<channel>``
scheme.
"""

from __future__ import annotations

from edge_protocol.ipc import (
    T_VR_HEALTH,
    T_VR_HELLO,
    T_VR_SET_CAMERAS,
    T_VR_STREAM_TOKEN,
    CameraHealth,
    IpcCameraSpec,
    SetCamerasPayload,
    WorkerHealthPayload,
)
from edge_protocol.messages import (
    BboxFramePayload,
    BboxPayload,
    CommandAckPayload,
    DeployModelPayload,
    DeviceCapabilities,
    HeartbeatPayload,
    LogPayload,
    StateReportPayload,
    StreamTokenReplyPayload,
    StreamTokenRequestPayload,
    TelemetryPayload,
    UpdateConfigPayload,
    ViolationPayload,
)
from edge_protocol.topics import (
    NS,
    SUB_ACK,
    SUB_BBOX,
    SUB_EVENTS,
    SUB_LOGS,
    SUB_STATE,
    SUB_STREAM_TOKEN,
    SUB_TELEMETRY,
    TOPIC_ACK,
    TOPIC_BBOX,
    TOPIC_CMD,
    TOPIC_EVENTS,
    TOPIC_LOGS,
    TOPIC_STATE,
    TOPIC_STREAM_TOKEN,
    TOPIC_TELEMETRY,
)
from edge_protocol.types import (
    T_BBOX_FRAME,
    T_COMMAND_ACK,
    T_DEPLOY_MODEL,
    T_HEARTBEAT,
    T_LOG,
    T_RESTART,
    T_RUN_DIAGNOSTICS,
    T_STATE_REPORT,
    T_STREAM_TOKEN_REQUEST,
    T_TELEMETRY,
    T_UPDATE_CONFIG,
    T_VIOLATION,
)

SCHEMA_VERSION = 1

__all__ = [
    # topics
    "NS",
    "SCHEMA_VERSION",
    "SUB_ACK",
    "SUB_BBOX",
    "SUB_EVENTS",
    "SUB_LOGS",
    "SUB_STATE",
    "SUB_STREAM_TOKEN",
    "SUB_TELEMETRY",
    "TOPIC_ACK",
    "TOPIC_BBOX",
    "TOPIC_CMD",
    "TOPIC_EVENTS",
    "TOPIC_LOGS",
    "TOPIC_STATE",
    "TOPIC_STREAM_TOKEN",
    "TOPIC_TELEMETRY",
    "T_BBOX_FRAME",
    "T_COMMAND_ACK",
    "T_DEPLOY_MODEL",
    # types
    "T_HEARTBEAT",
    "T_LOG",
    "T_RESTART",
    "T_RUN_DIAGNOSTICS",
    "T_STATE_REPORT",
    "T_STREAM_TOKEN_REQUEST",
    "T_TELEMETRY",
    "T_UPDATE_CONFIG",
    "T_VIOLATION",
    "T_VR_HEALTH",
    "T_VR_HELLO",
    "T_VR_SET_CAMERAS",
    "T_VR_STREAM_TOKEN",
    "BboxFramePayload",
    "BboxPayload",
    # agent <-> vision-runtime IPC
    "CameraHealth",
    "CommandAckPayload",
    "DeployModelPayload",
    "DeviceCapabilities",
    # payloads
    "HeartbeatPayload",
    "IpcCameraSpec",
    "LogPayload",
    "SetCamerasPayload",
    "StateReportPayload",
    "StreamTokenReplyPayload",
    "StreamTokenRequestPayload",
    "TelemetryPayload",
    "UpdateConfigPayload",
    "ViolationPayload",
    "WorkerHealthPayload",
]
