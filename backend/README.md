# AI Edge Ops — backend

Everything server-side lives here; the repo splits cleanly into `frontend/` and
`backend/`.

```
backend/
├── packages/svc_core/     dqh.svc_core — generic: messaging, config, http, presence, reconcile, errors
├── libs/edge_protocol/    edge_protocol — the server<->edge wire contract (payloads + topics)
├── server/                control plane: FastAPI + Postgres, operator API, AgentGateway
│   ├── compose.yml        server service (pulled into ../../docker-compose.yml)
│   └── mediamtx.yml       dev MediaMTX config
└── edge_agent/            runs on each edge device (Jetson): MQTT link, runtime, camera pipeline, local API
    └── compose.yml        edge-agent service (`edge` profile / standalone on a device)
```

The dev stack lives at the repo root: `docker-compose.yml` holds the infra
(db + emqx + minio + redis + mediamtx) and `include:`s the two package compose
files. Prod: `docker-compose.prod.yml` + `Caddyfile` + `mediamtx.prod.yml` (see
`DEPLOY.md`).

`server` and `edge_agent` both depend on `dqh-svc-core` and `edge-protocol`
(installed editable from `packages/` and `libs/`).

## Dev setup (uv workspace — one env for all five)

The repo root is a `uv` workspace (`[tool.uv.workspace]` in `/pyproject.toml`);
`server`, `edge_agent`, `libs/edge_protocol`, `packages/svc_core`,
`packages/ai_core` are members with a single root `uv.lock`.

```bash
uv sync --all-extras          # from the repo root — builds everything
```

Or plain pip (what CI and the Dockerfiles do):

```bash
cd backend && python -m venv .venv
.venv/Scripts/pip install -e "packages/svc_core[fastapi,mqtt,redis,sqlalchemy,security,dev]" \
                          -e "libs/edge_protocol[dev]" \
                          -e "server[dev]" \
                          -e "edge_agent[dev]"
```

## Test

```bash
cd backend/packages/svc_core   && uv run --all-extras pytest -q
cd backend/libs/edge_protocol  && uv run --extra dev pytest -q
cd backend/server              && uv run --extra dev pytest -q
cd backend/edge_agent          && uv run --extra dev pytest -q
```

## Run

```bash
# infra + control plane (from the repo root)
docker compose up --build                       # http://localhost:8000/docs

# + an edge node for an end-to-end demo (see docs/run-edge-agent.md)
DEVICE_ID=1 docker compose --profile edge up --build
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
