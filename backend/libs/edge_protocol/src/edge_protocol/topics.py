"""Topic scheme: ``fleet/devices/{device_id}/<channel>``."""

from __future__ import annotations

from dqh.svc_core.messaging import TopicTemplate

NS = "fleet"

TOPIC_STATE = TopicTemplate(f"{NS}/devices/{{device_id}}/state")
TOPIC_TELEMETRY = TopicTemplate(f"{NS}/devices/{{device_id}}/telemetry")
TOPIC_EVENTS = TopicTemplate(f"{NS}/devices/{{device_id}}/events")
TOPIC_CMD = TopicTemplate(f"{NS}/devices/{{device_id}}/cmd")
TOPIC_ACK = TopicTemplate(f"{NS}/devices/{{device_id}}/ack")

# wildcard patterns the server subscribes to
SUB_STATE = f"{NS}/devices/+/state"
SUB_TELEMETRY = f"{NS}/devices/+/telemetry"
SUB_EVENTS = f"{NS}/devices/+/events"
SUB_ACK = f"{NS}/devices/+/ack"

__all__ = [
    "NS",
    "SUB_ACK",
    "SUB_EVENTS",
    "SUB_STATE",
    "SUB_TELEMETRY",
    "TOPIC_ACK",
    "TOPIC_CMD",
    "TOPIC_EVENTS",
    "TOPIC_STATE",
    "TOPIC_TELEMETRY",
]
