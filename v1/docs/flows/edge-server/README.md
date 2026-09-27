# Edge ⇄ Server (MQTT control plane)

All control traffic between an edge box and the backend rides **MQTT**. Video does not
(see [../streaming/](../streaming/)).

Transport is chosen by `EDGE_TRANSPORT` (`memory` for tests/single process, `mqtt` for a
real deployment). `EdgePlane` (`app/edge/runtime.py`) owns the bus + `AgentGateway`.

## Envelope

Every MQTT message is a JSON `Envelope` (`dqh.svc_core.messaging`):

```json
{ "id": "…", "type": "device.heartbeat", "source": "cam-plant-a-01", "correlation_id": null, "payload": {} }
```

`type` — discriminator (`edge_protocol/types.py`); `payload` schemas — `edge_protocol/messages.py`.
`AgentGateway` routes inbound via a `MessageRouter` keyed on `type`.

## Topic map

Scheme `agent/devices/{device_id}/<channel>`; server subscribes with `+` wildcards.

| Direction | Topic | `type` | Payload | Flow |
|---|---|---|---|---|
| edge → server | `…/state` | `device.heartbeat` | `HeartbeatPayload` | [heartbeat](heartbeat.md) |
| edge → server | `…/state` | `device.state` | `StateReportPayload` | [deploy-model](deploy-model.md) |
| edge → server | `…/telemetry` | `device.telemetry` | `TelemetryPayload` | [telemetry](telemetry.md) |
| edge → server | `…/events` | `device.violation` | `ViolationPayload` | [../inference/violation-alert](../inference/violation-alert.md) |
| edge → server | `…/logs` | `device.log` | `LogPayload` | [logs](logs.md) |
| edge → server | `…/bbox` | `device.bbox_frame` | `BboxFramePayload` | [../inference/bbox-overlay](../inference/bbox-overlay.md) |
| edge ↔ server (RPC) | `…/stream_token` | `device.stream_token_request` | `StreamTokenRequestPayload` → `StreamTokenReplyPayload` | [../streaming/edge-publish](../streaming/edge-publish.md) |
| server → edge | `…/cmd` | `command.deploy_model` | `DeployModelPayload` | [deploy-model](deploy-model.md) |
| server → edge | `…/cmd` | `command.update_config` | `UpdateConfigPayload` | [update-config](update-config.md) |
| server → edge | `…/cmd` | `command.restart` / `command.run_diagnostics` | — | [command-ack](command-ack.md) |
| edge → server | `…/ack` | `command.ack` | `CommandAckPayload` | [command-ack](command-ack.md) |

MQTT Last-Will: the edge registers a `device.state` with `runtime_status: "offline"` on
`…/state`, so an ungraceful disconnect is visible.

> **Caveat (current code):** `AgentGateway.start()` subscribes to `state`, `telemetry`,
> `events`, `logs`, `bbox`, and binds the `stream_token` RPC. It does **not** yet
> subscribe to `…/ack` — see [command-ack.md](command-ack.md).

## WebSocket channels (server → browser)

| Route | Hub topic | Frames |
|---|---|---|
| `GET /api/v1/agent/ws/telemetry` | `telemetry/#` | `telemetry.device`, `telemetry.agent`. `{"op":"snapshot"}` on connect replays current values. |
| `GET /api/v1/agent/ws/logs` | `logs/#` | `device.log` |
| `GET /api/v1/ws/alerts` | `alerts/#` | `alert.created` |
| *(bbox)* | `bbox/{camera_id}` | `device.bbox_frame` |

Auth before `accept()` via `authenticate_ws` — see [../frontend/websocket.md](../frontend/websocket.md).
Multi-replica: `REALTIME_TRANSPORT=redis` (`RedisPubSubMessageBus`).
