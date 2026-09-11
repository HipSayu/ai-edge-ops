from __future__ import annotations

from dqh.svc_core.messaging import Envelope, topic_matches

import edge_protocol as p


def test_topic_render_and_wildcard():
    topic = p.TOPIC_STATE.render(device_id="dev-1")
    assert topic == "agent/devices/dev-1/state"
    assert topic_matches(p.SUB_STATE, topic)
    assert p.TOPIC_STATE.parse(topic) == {"device_id": "dev-1"}


def test_envelope_with_payload_roundtrips():
    env = Envelope(
        type=p.T_HEARTBEAT,
        source="dev-1",
        payload=p.HeartbeatPayload(fps=24.0, inference_latency_ms=12.0).model_dump(mode="json"),
    )
    raw = env.model_dump(mode="json")
    back = Envelope[p.HeartbeatPayload].model_validate(raw)
    assert back.payload.fps == 24.0
    assert back.type == p.T_HEARTBEAT
