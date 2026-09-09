# Streaming flows (WebRTC)

Raw camera video goes **edge → MediaMTX → browser** over WebRTC — WHIP to ingest, WHEP
to play. It never touches the FastAPI process or MQTT; the backend only issues and
verifies short-lived tokens that say *who may publish/read which camera path*.

## Tokens

`StreamingService` mints an HS256 JWT: `{ "type": "stream", "path": "cam_{id}",
"action": "publish|read", "iat", "exp" }`, TTL `STREAM_TOKEN_SECONDS` (default 30 s),
signed with `JWT_SECRET`. `path` = `cam_{camera_id}` where `camera_id` is
`app.modules.camera.Camera.id`.

| Caller | How it gets a token | Auth basis |
|---|---|---|
| Edge agent (publish) | MQTT RPC → `AgentGateway._on_stream_token_request` | the MQTT link is already broker-authenticated; edge has no HTTP credential |
| Operator (publish, manual) | `GET /streaming/cameras/{id}/publish-token` | `require_permission("cameras.stream.publish")` |
| Browser (view) | `GET /streaming/cameras/{id}/view-token` | `require_permission("cameras.stream.view")` |

## MediaMTX auth webhook

MediaMTX runs `authMethod: http` and calls `POST /api/v1/streaming/auth` before every
publish and read. Handler accepts only `action ∈ {publish, read}` with a JWT whose
`type`/`path`/`action` claims match; everything else → `401` (deny by default).

| Flow | File |
|---|---|
| Edge publishes a camera | [edge-publish.md](edge-publish.md) |
| Frontend views a camera | [frontend-view.md](frontend-view.md) |
