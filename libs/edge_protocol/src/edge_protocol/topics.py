"""Topic scheme: ``agent/devices/{device_id}/<channel>``."""

from __future__ import annotations

from dqh.svc_core.messaging import TopicTemplate

NS = "agent"

TOPIC_STATE = TopicTemplate(f"{NS}/devices/{{device_id}}/state")
TOPIC_TELEMETRY = TopicTemplate(f"{NS}/devices/{{device_id}}/telemetry")
TOPIC_EVENTS = TopicTemplate(f"{NS}/devices/{{device_id}}/events")
TOPIC_LOGS = TopicTemplate(f"{NS}/devices/{{device_id}}/logs")
TOPIC_CMD = TopicTemplate(f"{NS}/devices/{{device_id}}/cmd")
TOPIC_ACK = TopicTemplate(f"{NS}/devices/{{device_id}}/ack")
TOPIC_BBOX = TopicTemplate(f"{NS}/devices/{{device_id}}/bbox")
TOPIC_STREAM_TOKEN = TopicTemplate(f"{NS}/devices/{{device_id}}/stream_token")

# wildcard patterns the server subscribes to
SUB_STATE = f"{NS}/devices/+/state"
SUB_TELEMETRY = f"{NS}/devices/+/telemetry"
SUB_EVENTS = f"{NS}/devices/+/events"
SUB_LOGS = f"{NS}/devices/+/logs"
SUB_ACK = f"{NS}/devices/+/ack"
SUB_BBOX = f"{NS}/devices/+/bbox"
SUB_STREAM_TOKEN = f"{NS}/devices/+/stream_token"

__all__ = [
    "NS",
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
]
