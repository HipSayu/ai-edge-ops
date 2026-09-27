# Frontend ⇄ Server flows

The React SPA talks to the backend three ways: **REST** for queries/commands,
**WebSocket** for live telemetry/alerts/logs, **WHEP** for video
([../streaming/frontend-view.md](../streaming/frontend-view.md)).

| Flow | File |
|---|---|
| REST call + token refresh | [rest-auth.md](rest-auth.md) |
| WebSocket subscribe | [websocket.md](websocket.md) |

## Service ↔ router map

| `shared/api/services/*` | Backend router | Used by |
|---|---|---|
| `auth` | `/auth` | login, refresh |
| `agent` | `/agent` | `modules/agent` |
| `ai` | `/model-registry`, `/deployments` | `modules/ai` |
| `observability` | `/violations`, `/alerts`, `/analytics/*` | `modules/observability`, `modules/overview` |
| `system` | `/system` | `modules/system` |
| `user` | `/users` | `modules/system` |
| `assistant` | `/assistant` | `modules/assistant` |
| *(streaming)* | `/streaming/cameras/{id}/view-token` | `LiveMonitorPanel` |
