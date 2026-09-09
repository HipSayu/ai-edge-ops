# System Architecture

## Actors and transports

```mermaid
flowchart LR
    subgraph EDGE["Edge box (one per site)"]
        EA["Edge Agent<br/>capture · inference · PPE rules"]
        FF["ffmpeg WHIP publisher<br/>(one per camera)"]
    end

    subgraph INFRA["Infrastructure"]
        MQ["MQTT Broker<br/>(EMQX)"]
        MTX["MediaMTX<br/>WebRTC SFU"]
        PG[("PostgreSQL")]
        REG[("OCI registry<br/>model images")]
        RD[("Redis<br/>WS fan-out")]
    end

    subgraph SERVER["Backend Server (FastAPI, N replicas)"]
        GW["AgentGateway<br/>edge protocol"]
        MOD["Domain modules<br/>agent · deployment · model_registry<br/>observability · camera · streaming · ..."]
        WSH["WebSocket hub"]
        REST["REST API"]
    end

    subgraph CLIENT["Browser SPA"]
        UI["React app"]
    end

    EA <-->|"MQTT pub/sub + RPC"| MQ
    MQ <--> GW
    FF -->|"WHIP (WebRTC ingest)"| MTX
    MTX -->|"WHEP (WebRTC playback)"| UI
    MTX -->|"auth webhook (HTTP)"| REST
    GW --> MOD --> PG
    MOD -->|"catalog / tags / digests"| REG
    EA -->|"docker compose pull (model image)"| REG
    EA -->|"evidence upload (HTTP)"| REST
    WSH <-->|"pub/sub"| RD
    UI <-->|"REST (JSON)"| REST
    UI <-->|"WebSocket (Envelope frames)"| WSH
```

| Link | Transport | Payload | Guarantees |
|---|---|---|---|
| Edge ⇄ Server control plane | MQTT (`agent/devices/{id}/*`) | JSON `Envelope` | at-least-once; commands/violations must not drop |
| Edge → Server (stream token) | MQTT request/reply (RPC) | `StreamTokenRequest` / `StreamTokenReply` | reuses the authenticated MQTT link |
| Edge → Server (evidence) | HTTP | multipart JPEG upload | retryable, idempotent |
| Edge → MediaMTX | WHIP (WebRTC / RTP) | raw H.264 video, one session per camera | best-effort, lossy |
| MediaMTX → Browser | WHEP (WebRTC / RTP) | same video | best-effort, lossy |
| Server ⇄ Browser (queries/commands) | HTTP REST, `ApiResponse` envelope | JSON | request/response |
| Server → Browser (live) | WebSocket, JSON `Envelope` text frames | telemetry / alerts / logs / bbox | best-effort, latest-wins |
| Server replica ⇄ replica (live fan-out) | Redis pub/sub (optional) | `Envelope` | best-effort |

Design rule: **anything needing delivery guarantees (commands, ACKs, violations) rides MQTT or the DB; anything latest-wins (metric samples, bbox overlays, log lines) rides the WS hub / Redis and a dropped frame is corrected by the next one.**

## Backend module map

`backend/server/app`:

```
main.py            FastAPI lifespan: configure logging, init_db, register_event_handlers,
                   connect ws_hub, start EdgePlane
core/
  config.py        single Settings object (env: DB__* MQTT__* REDIS__*)
  database.py      async SQLAlchemy session + init_db (creates tables on boot)
  events.py        in-process event_bus (publish/subscribe dataclasses)
  ws.py            ws_hub = build_realtime_bus()  (memory | redis)
  ws_auth.py       authenticate_ws: ?token= or Bearer -> User, before accept()
  messaging/       redis_bus.py: cross-replica pub/sub MessageBus for the hub
  auth.py          JWT decode, require_permission dependency
edge/
  runtime.py       EdgePlane: owns the edge MessageBus (memory | mqtt) + AgentGateway
  gateway.py       AgentGateway: MQTT <-> app services; MessageRouter by Envelope.type
domain/
  fleet_registry.py  FleetRegistry: in-memory reported state (online/health/image) + metric ring
  reconcile/       generic desired-vs-observed diff -> Plan of CREATE/UPDATE/DELETE
modules/<name>/    router.py (HTTP/WS) · service.py (use-cases) · repository.py (DB)
                   models.py (ORM) · schemas.py (pydantic) · event.py (published events)
                   domain.py (enums/rules) · handlers.py / integration.py / realtime.py (subscribers)
api/router.py      mounts every module router under /api/v1
```

Modules: `auth`, `user`, `system`, `access_control`, `agent` (device config + FleetRegistry + metric ring),
`model_registry` (GHCR catalog, no DB), `deployment` (deploy = command),
`observability` (violations + alerts + analytics),
`camera`, `streaming`, `assistant`.

### Module boundaries

- A module reaches another module only through its **public `service.py`**, never its repository.
- Cross-module reactions go through `core.events.event_bus` — a synchronous in-process
  publish/subscribe of frozen dataclasses. Publishers publish *after their own commit*;
  subscribers open their own `session_scope()`.

### Event bus wiring (`register_event_handlers`)

```mermaid
flowchart TD
    HB["HeartbeatRecorded"] --> TR["telemetry_relay<br/>fan telemetry to ws_hub"]
    VR["ViolationRecorded"] --> AH["agent.handlers<br/>bump device.last_seen_at"]
    VR --> OI["observability.integration<br/>raise PPE_VIOLATION alert"]
    DWO["DeviceWentOffline"] --> OI2["observability.integration<br/>DEVICE_OFFLINE alert"]
    DLD["DeviceLatencyDegraded"] --> OI3["observability.integration<br/>LATENCY_DEGRADED alert"]
    DF["DeploymentFailed"] --> OI4["observability.integration<br/>DEPLOYMENT_FAILED alert"]
    AR["AlertRaised"] --> ORL["observability.realtime<br/>push alert.created to ws_hub"]
    DR["DeployRequested"] --> GW["AgentGateway<br/>send MQTT T_DEPLOY_MODEL"]
    DCC["DeviceConfigChanged"] --> DS["deployment.subscribers<br/>resolve -> ConfigResolved"]
    CR["ConfigResolved"] --> GW2["AgentGateway<br/>send MQTT T_UPDATE_CONFIG"]
```

| Event | Publisher | Subscribers |
|---|---|---|
| `HeartbeatRecorded` | `AgentService.record_heartbeat` | `telemetry_relay` → WS `telemetry/{id}` + `telemetry/agent` |
| `DeviceLatencyDegraded` | `AgentService.record_heartbeat` (status → DEGRADED) | `observability.integration` → alert |
| `DeviceWentOffline` | `AgentGateway.sweep_presence` (from `fleet.sweep()`) | `observability.integration` → alert |
| `DeviceConfigChanged` | `AgentService.update_device` (inference/cameras) | `deployment.subscribers` → resolve → `ConfigResolved` |
| `ViolationRecorded` | `ViolationService.record` | `observability.integration` → alert |
| `AlertRaised` | `AlertService.raise_alert` | `observability.realtime` → WS `alerts/{severity}` |
| `DeployRequested` | `DeployService.deploy` | `AgentGateway` → MQTT `T_DEPLOY_MODEL` |
| `ConfigResolved` | `deployment.subscribers` | `AgentGateway` → MQTT `T_UPDATE_CONFIG` |
| `DeploymentFailed` | `AgentGateway` (deploy send failure) | `observability.integration` → alert |

## Edge agent module map

`backend/edge_agent/src/edge_agent`:

```
main.py            wires bus + link + agent + backend + telemetry pump + local API, runs forever
core/
  config.py        AgentSettings; device_id (string), cameras[], mqtt, vision
  hardware.py      detect_hardware(): arch, accelerators, encoders, model formats -> DeviceCapabilities
  identity.py      agent_version / primary_ip / uptime_s
  state.py         StateStore: desired vs reported model state, persisted to state.json
network/
  link.py          EdgeLink: heartbeat loop out, command subscription in, ACK back, RPC client
  api.py           local HTTP API (:9100) for a field technician / probes
services/
  agent.py         Agent: executes commands (deploy/update_config/restart/diagnostics), reconcile loop
  backend.py       VisionBackend seam: ComposedBackend (cv2 + ffmpeg) | DeepStreamBackend (Jetson)
  pipeline.py      CameraPipeline: frame -> runtime.infer -> evaluate_ppe -> violation + bbox frame
  telemetry.py     TelemetryPump: fast metric samples (~1s) batched to link.send_telemetry
  evidence.py      HttpEvidenceUploader: POST selected JPEG to server /evidence
  (model images: the agent runs docker compose pull — no artifact download)
runtime/           InferenceRuntime: yolo | dummy
streaming/         VideoPublisher: ffmpeg_whip (WHIP via `ffmpeg -f whip`) | null
analytics/ppe.py   detections -> violation types (no_helmet, ...)
```

## Data stores

| Store | Holds | Notes |
|---|---|---|
| PostgreSQL | **desired** device config (`devices`: name/site/labels/desired_image/cameras/inference), violations, snapshots, alerts, users/roles, audit_logs, app_settings, cameras | `init_db()` on boot; reference DDL in `backend/schema.sql`. No models / deployments / metric_samples tables. |
| FleetRegistry (in-memory) | **reported** device state: online / health / running image / probed hw + a ~15-min metric ring buffer | not persisted; rebuilt from MQTT heartbeats + `state` on every server start. See [`REFACTOR_stateless.md`](REFACTOR_stateless.md). |
| Container registry (GHCR) | the model catalog — each model version is one multi-arch OCI image; metadata in `ai.edge-ops.model.*` labels | `ModelCatalog` reads it live (v2 API); edge deploys by `docker compose pull` |
| Local disk (server) | evidence images (`settings.evidence_dir`) | served from `/evidence/{filename}` |
| Local disk (edge) | `state.json` (desired/reported), downloaded model weights, outbox | survives restart; drives reconcile |
| Redis | transient WS pub/sub only | no durable data; used when `REALTIME_TRANSPORT=redis` |
| MediaMTX | in-flight WebRTC tracks | no persistence |

## Deployment topology

All compose lives in `app/deploy/`. Local dev — from `deploy/`:

```
export COMPOSE_ENV_FILES=.env.infra,.env.app
docker compose -f compose.infra.yml up -d          # Postgres, EMQX, Redis, MediaMTX
docker compose up --build                          # + server (compose.yml includes the infra)
COMPOSE_ENV_FILES=.env.infra,.env.app,.env.edge \
  docker compose --profile edge up --build         # + edge-agent + inference (end-to-end)
```

`compose.yml` `include:`s `compose.infra.yml`. Prod = `compose.infra.yml` +
`compose.app.yml` (Caddy + frontend + server). Config is per concern:
`.env.infra` / `.env.app` / `.env.edge` — compose files are pure `${VAR}`
templates with no fallbacks. A backing-services-only VPS runs `compose.infra.yml`
plus the `deploy/vps-proxy/` system-nginx snippets.
