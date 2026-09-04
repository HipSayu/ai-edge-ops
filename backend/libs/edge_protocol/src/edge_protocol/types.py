"""Message-type discriminators carried in ``Envelope.type``."""

from __future__ import annotations

# edge -> server
T_HEARTBEAT = "device.heartbeat"
T_TELEMETRY = "device.telemetry"
T_STATE_REPORT = "device.state"
T_VIOLATION = "device.violation"
T_COMMAND_ACK = "command.ack"

# server -> edge
T_DEPLOY_MODEL = "command.deploy_model"
T_UPDATE_CONFIG = "command.update_config"
T_RESTART = "command.restart"
T_RUN_DIAGNOSTICS = "command.run_diagnostics"

__all__ = [
    "T_COMMAND_ACK",
    "T_DEPLOY_MODEL",
    "T_HEARTBEAT",
    "T_RESTART",
    "T_RUN_DIAGNOSTICS",
    "T_STATE_REPORT",
    "T_TELEMETRY",
    "T_UPDATE_CONFIG",
    "T_VIOLATION",
]
