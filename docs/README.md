# Architecture docs

- [ARCHITECTURE.md](ARCHITECTURE.md) — system map: actors, transports, data stores, backend module + event-bus wiring.
- [flows/](flows/) — one file per business flow, grouped by domain.

## Actors

- **Edge Agent** (`edge_agent`) — captures cameras, runs inference locally, publishes state/events over MQTT, streams video over WHIP. One process per edge box.
- **Backend Server** (`server`) — FastAPI. REST API + business logic + persistence + WebSocket hub for dashboards + MQTT gateway for edges. Stateless.
- **Infrastructure** — MQTT broker (EMQX), PostgreSQL, MinIO/S3, Redis (cross-replica WS fan-out), MediaMTX (WebRTC SFU).
- **Frontend** (`ui`) — React SPA. REST for commands/queries, WebSocket for live telemetry/alerts/logs, WHEP for video.

Shared wire contract: `libs/edge_protocol` (`topics.py`, `types.py`, `messages.py`), imported by both edge and server.

## Flow index

| Domain | Flow | File |
|---|---|---|
| edge ⇄ server (MQTT) | Health heartbeat (15 s) | [flows/edge-server/heartbeat.md](flows/edge-server/heartbeat.md) |
| | Fast telemetry (batched) | [flows/edge-server/telemetry.md](flows/edge-server/telemetry.md) |
| | Log stream | [flows/edge-server/logs.md](flows/edge-server/logs.md) |
| | Device offline / presence | [flows/edge-server/device-offline.md](flows/edge-server/device-offline.md) |
| | Deploy model | [flows/edge-server/deploy-model.md](flows/edge-server/deploy-model.md) |
| | Update config | [flows/edge-server/update-config.md](flows/edge-server/update-config.md) |
| | Command ACK + reconcile | [flows/edge-server/command-ack.md](flows/edge-server/command-ack.md) |
| inference | Live bbox overlay | [flows/inference/bbox-overlay.md](flows/inference/bbox-overlay.md) |
| | Violation → alert | [flows/inference/violation-alert.md](flows/inference/violation-alert.md) |
| | Evidence upload / fetch | [flows/inference/evidence.md](flows/inference/evidence.md) |
| streaming (WebRTC) | Edge publishes a camera | [flows/streaming/edge-publish.md](flows/streaming/edge-publish.md) |
| | Frontend views a camera | [flows/streaming/frontend-view.md](flows/streaming/frontend-view.md) |
| frontend ⇄ server | REST call + token refresh | [flows/frontend/rest-auth.md](flows/frontend/rest-auth.md) |
| | WebSocket subscribe | [flows/frontend/websocket.md](flows/frontend/websocket.md) |

Topic map, Envelope contract, and WS channel table live in
[flows/edge-server/README.md](flows/edge-server/README.md).
