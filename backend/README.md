# AI Edge Ops — backend

Everything server-side lives here; the repo splits cleanly into `frontend/` and
`backend/`.

```
backend/
├── packages/svc_core/     dqh.svc_core — generic: messaging, config, http, presence, reconcile, errors
├── libs/edge_protocol/    edge_protocol — the server<->edge wire contract (payloads + topics)
├── server/                control plane: FastAPI + Postgres, operator API, AgentGateway
├── edge_agent/            runs on each edge device (Jetson): MQTT link, runtime, camera pipeline, local API
└── deploy/
    ├── server/docker-compose.yml   db + emqx + minio + redis + server
    └── edge/docker-compose.yml     edge-agent (points at a central broker)
```

`server` and `edge_agent` both depend on `dqh-svc-core` and `edge-protocol`
(installed editable from `packages/` and `libs/`).

## Dev setup (one venv for all four)

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -e "packages/svc_core[fastapi,mqtt,dev]" \
                          -e "libs/edge_protocol[dev]" \
                          -e "server[dev]" \
                          -e "edge_agent[dev]"
```

## Test

```bash
cd backend/packages/svc_core   && ../../.venv/Scripts/python -m pytest -q   # 29
cd backend/libs/edge_protocol  && ../../.venv/Scripts/python -m pytest -q   # 2
cd backend/server              && ../.venv/Scripts/python -m pytest -q      # 11
cd backend/edge_agent          && ../.venv/Scripts/python -m pytest -q      # 7
```

## Run

```bash
# control plane
cd backend/deploy/server && docker compose up --build      # http://localhost:8000/docs

# an edge node (see docs/run-edge-agent.md for the full guide)
cd backend/deploy/edge && DEVICE_ID=1 MQTT_HOST=host.docker.internal docker compose up --build
```

## The server

Modular monolith, package-by-feature. One module per bounded context under
`server/app/modules/<name>/` — `router → service → repository → model`, plus
`domain.py` (enums/events/rules) and `events.py` (subscribers). Modules talk only
via **public services** or **in-process domain events** (`app/core/events.py`).

Built on **`dqh.svc_core`**: `create_app` + `ApiResponse` envelope
(`{ success, data, error, request_id }`) + error taxonomy + pagination + the
messaging bus. Device traffic crosses `server/app/edge/` over a `dqh.svc_core`
MessageBus (`memory` in dev/tests, `mqtt` in prod via `EDGE_TRANSPORT`).

Schema is created on startup (`init_db`). Swap for Alembic when it stabilises.

## Config

One `Settings` object, nested groups from `dqh.svc_core.config`, env with `__`:
`DB__URL`, `MQTT__HOST`, `S3__ENDPOINT_URL`, `REDIS__URL`, `CORS_ORIGINS`,
`OFFLINE_THRESHOLD_SECONDS`, `EDGE_TRANSPORT`.
