# AI Edge Ops

Control plane (FastAPI) + edge agent + operator dashboard (React) for real-time
PPE detection.

```
app/
├── deploy/            all docker compose lives here
│   ├── compose.infra.yml   backing services (db, redis, mqtt, mediamtx) — the base
│   ├── compose.yml          DEV: includes infra + server + edge-agent + inference
│   ├── compose.app.yml      PROD overlay: Caddy + frontend + server (GHCR images)
│   ├── compose.edge.yml     a real edge device (agent + inference, no infra)
│   ├── .env.infra.example    ┐  one file per concern — copy each to .env.<name>
│   ├── .env.app.example      │  compose files are pure ${VAR} templates:
│   ├── .env.edge.example     ┘  no literals, no fallbacks
│   ├── config/              Caddyfile, mediamtx.yml
│   └── vps-proxy/           system-nginx snippets to expose an infra-only VPS
├── server/              FastAPI control plane        (server/Dockerfile)
├── edge_agent/          host supervisor per device   (edge_agent/Dockerfile)
├── inference/           vision runtime, swapped per model deploy
├── libs/edge_protocol/  server <-> edge wire contract
├── packages/            svc_core, ai_core (shared libs)
├── ui/                  React SPA (Vite dev / nginx image in prod)
└── DEPLOY.md                production runbook
```

---

## Prerequisites

- Docker + Docker Compose **v2.24+** (`include:` + object `env_file` + inline
  env-file comments)
- `git submodule update --init --recursive` — private `svc_core` / `ai_core`
- Node 20+ and `uv` — only for running the UI / backend packages outside Docker

---

## Config — one env file per concern

Compose files hold **no literal values and no fallbacks** — every `${VAR}` must
come from an env file. There are three, by concern:

| file | feeds | used by |
|---|---|---|
| `.env.infra` | db / redis / mqtt / mediamtx creds + host ports | every stack |
| `.env.app` | server settings, JWT, prod image/domain | dev + prod |
| `.env.edge` | `DEVICE_ID`, agent MQTT target, cameras, inference image | edge |

```bash
cd deploy
cp .env.infra.example .env.infra
cp .env.app.example   .env.app
cp .env.edge.example  .env.edge      # only if running an edge node
```

`.env.*` are git-ignored; the `.example` files list every key with a `prod:` /
`device:` note. Compose loads them via **`COMPOSE_ENV_FILES`** (comma-separated,
later wins) — for dev, export all three (silences unset-var warnings from the
`edge` profile):

```bash
export COMPOSE_ENV_FILES=.env.infra,.env.app,.env.edge     # put this in your shell rc
```

---

## Run — dev

From `app/deploy/`, with `COMPOSE_ENV_FILES` exported as above:

| Command | What it does |
|---|---|
| `docker compose up --build` | infra (db, redis, mqtt, mediamtx) + server, live reload |
| `docker compose --profile edge up --build` | the above **+** edge-agent + inference sidecar (full pipeline on one box) |
| `docker compose -f compose.infra.yml up -d` | infra only — for running the server/agent from source |
| `docker compose down` | stop, keep volumes |
| `docker compose down -v` | stop, drop `pgdata` / `redisdata` / edge state |

The UI is not in compose — run it from `app/ui`:

```bash
npm install
npm run dev            # http://localhost:5173, proxies /api/v1 -> :8000
```

| Service | URL |
|---|---|
| API + docs | http://localhost:8000/docs |
| Dashboard (Vite) | http://localhost:5173 |
| EMQX dashboard | http://localhost:58083 — `admin` / `EMQX_DASHBOARD_PASSWORD` |
| Edge agent API | http://localhost:9100/status |

Host ports sit in the 5xxxx range (`DB_PORT=55432`, …) so they don't collide
with a system Postgres/Redis; change them in `.env`.

---

## Run — an edge device

`compose.edge.yml` is standalone (no infra — it dials a remote broker). The
agent shells out to `docker compose` itself for model deploys, so on the device
the file must be named `compose.yml`:

```bash
mkdir -p /opt/ai-edge-ops && cd /opt/ai-edge-ops
scp  <you>@dev:app/deploy/compose.edge.yml   ./compose.yml
scp  <you>@dev:app/deploy/.env.edge.example  ./.env.edge
$EDITOR .env.edge    # DEVICE_ID, AGENT_MQTT_HOST/PORT/TLS, AGENT_CAMERAS
export COMPOSE_ENV_FILES=.env.edge
docker compose up -d
docker compose logs -f edge
```

Jetson: use `inference/Dockerfile.jetson` (DeepStream) and set
`INFERENCE_RUNTIME`.

---

## Run — prod

Layered: infra base **+** app overlay. On the deploy host:

```bash
cd /opt/ai-edge-ops
cp .env.infra.example .env.infra  &&  cp .env.app.example .env.app
$EDITOR .env.infra .env.app   # POSTGRES_PASSWORD, JWT_SECRET, MQTT_*, DOMAIN,
                              # SERVER_ENVIRONMENT=production, SERVER_MQTT_TLS=true, ...
export COMPOSE_FILE=compose.infra.yml:compose.app.yml
export COMPOSE_ENV_FILES=.env.infra,.env.app
docker compose pull
docker compose up -d
```

CI (`.github/workflows/deploy.yml`) builds the GHCR images and ships
`compose.infra.yml` + `compose.app.yml` + `config/` to `/opt/ai-edge-ops` on
every push to `main`. TLS, MQTT mTLS, schema, rollback, backups: **[`DEPLOY.md`](DEPLOY.md)**.

VPS running backing services only: `docker compose -f compose.infra.yml up -d`
plus the `deploy/vps-proxy/` nginx snippets — see `deploy/vps-proxy/README.md`.

---

## Build images

CI publishes two; the build context for the server is the repo root (it bundles
the shared libs):

```bash
docker build -t ghcr.io/hopquangdo/ai-edge-ops-server:dev   -f server/Dockerfile   .
docker build -t ghcr.io/hopquangdo/ai-edge-ops-frontend:dev  ui
docker build -t ai-edge-ops/edge:dev -f edge_agent/Dockerfile .
docker build -t ai-edge-ops/inference:dev  -f inference/Dockerfile .
```

`docker compose build` drives the same Dockerfiles.

---

## Test

One `uv sync` at the repo root builds every backend package into a shared env:

```bash
uv sync
uv run --packages dqh-svc-core   pytest -q
uv run --packages edge-protocol  pytest -q
uv run --packages server         pytest -q
uv run --packages edge_agent     pytest -q
uv run --packages inference      pytest -q

cd ui && npm run lint && npm run build
```

## Backend packages — dev setup

`server`, `edge_agent`, `libs/edge_protocol`, `packages/svc_core`,
`packages/ai_core` are members of the root `uv` workspace with a single
`uv.lock`:

```bash
uv sync --all-extras          # from the repo root — builds everything
```

Or plain pip (what CI and the Dockerfiles do):

```bash
python -m venv .venv
.venv/Scripts/pip install -e "packages/svc_core[fastapi,mqtt,redis,sqlalchemy,security,dev]" \
                          -e "libs/edge_protocol[dev]" \
                          -e "server[dev]" \
                          -e "edge_agent[dev]"
```
