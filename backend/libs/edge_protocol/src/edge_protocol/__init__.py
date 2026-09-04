"""AI Edge Ops server<->edge contract — shared by ``server`` and ``edge_agent``.

Payloads travel as ``dqh.svc_core.messaging.Envelope[<Payload>]``; ``Envelope.type``
is one of the ``T_*`` constants; topics follow the ``fleet/devices/{id}/<channel>``
scheme.
"""

from __future__ import annotations

from edge_protocol.messages import (
    CommandAckPayload,
    DeployModelPayload,
    HeartbeatPayload,
    StateReportPayload,
    TelemetryPayload,
    UpdateConfigPayload,
    ViolationPayload,
)
from edge_protocol.topics import (
    NS,
    SUB_ACK,
    SUB_EVENTS,
    SUB_STATE,
    SUB_TELEMETRY,
    TOPIC_ACK,
    TOPIC_CMD,
    TOPIC_EVENTS,
    TOPIC_STATE,
    TOPIC_TELEMETRY,
)
from edge_protocol.types import (
    T_COMMAND_ACK,
    T_DEPLOY_MODEL,
    T_HEARTBEAT,
    T_RESTART,
    T_RUN_DIAGNOSTICS,
    T_STATE_REPORT,
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
    "SUB_EVENTS",
    "SUB_STATE",
    "SUB_TELEMETRY",
    "TOPIC_ACK",
    "TOPIC_CMD",
    "TOPIC_EVENTS",
    "TOPIC_STATE",
    "TOPIC_TELEMETRY",
    "T_COMMAND_ACK",
    "T_DEPLOY_MODEL",
    # types
    "T_HEARTBEAT",
    "T_RESTART",
    "T_RUN_DIAGNOSTICS",
    "T_STATE_REPORT",
    "T_TELEMETRY",
    "T_UPDATE_CONFIG",
    "T_VIOLATION",
    "CommandAckPayload",
    "DeployModelPayload",
    # payloads
    "HeartbeatPayload",
    "StateReportPayload",
    "TelemetryPayload",
    "UpdateConfigPayload",
    "ViolationPayload",
]
