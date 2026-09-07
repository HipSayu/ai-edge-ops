# AI Edge Ops

Control plane + edge agent + operator dashboard for real-time PPE detection.

```
app/
├── docker-compose.yml        dev stack: infra + server (+ edge-agent under `edge` profile)
├── docker-compose.prod.yml   prod stack: GHCR images behind Caddy
├── Caddyfile  mediamtx.prod.yml   prod support files (shipped to the deploy host by CI)
├── DEPLOY.md                 full production runbook
├── backend/
│   ├── packages/svc_core/    shared lib (private submodule)
│   ├── libs/edge_protocol/   server <-> edge wire contract
│   ├── server/               FastAPI control plane        — server/compose.yml, server/Dockerfile
│   └── edge_agent/           runs on each Jetson device    — edge_agent/compose.yml, edge_agent/Dockerfile
└── frontend/                 React SPA (nginx)            — frontend/Dockerfile
```

Config is per level: `app/.env` (shared infra creds), `backend/server/.env`,
`backend/edge_agent/.env`. Copy each `*.env.example` and edit. `.env` files are
git-ignored.

---

## Prerequisites

- Docker + Docker Compose v2.24+ (needs `include:` and the object `env_file` form)
- For the private `svc_core` submodule: `git submodule update --init --recursive`

---

## Run — dev (local)

Everything from this directory (`app/`).

```bash
cp .env.example .env                       # optional — defaults work
cp backend/server/.env.example backend/server/.env

# infra (postgres, emqx, minio, redis, mediamtx) + server, with live reload
docker compose up --build
```

| Service | URL |
|---|---|
| API + docs | http://localhost:8000/docs |
| EMQX dashboard | http://localhost:18083 — `admin` / `public` |
| MinIO console | http://localhost:9001 — `minioadmin` / `minioadmin` |

Add an edge agent for an end-to-end demo (talks to the compose `mqtt` + `server`):

```bash
cp backend/edge_agent/.env.example backend/edge_agent/.env
DEVICE_ID=1 docker compose --profile edge up --build edge-agent
# local agent API: http://localhost:9100/status
```

Stop / wipe:

```bash
docker compose --profile edge down          # keep volumes
docker compose --profile edge down -v       # drop pgdata / miniodata / state
```

---

## Build images

The two images CI publishes to GHCR:

```bash
# server  — build context is backend/ (bundles svc_core + edge_protocol)
docker build -t ghcr.io/hopquangdo/ai-edge-ops-server:dev \
  -f backend/server/Dockerfile backend

# frontend — static SPA served by nginx
docker build -t ghcr.io/hopquangdo/ai-edge-ops-frontend:dev frontend
```

Edge-agent image (not in CI — operators build/pull it per device):

```bash
docker build -t ai-edge-ops/edge-agent:dev \
  -f backend/edge_agent/Dockerfile backend
```

`docker compose build` (dev) and `docker compose -f docker-compose.prod.yml`
(prod) drive these same Dockerfiles.

> Jetson: swap the `edge_agent/Dockerfile` base for an `l4t-pytorch` image and
> install the `[inference]` extra (real YOLO via the vendored
> `backend/edge_agent/package/ultralytics`).

---

## Run — prod

Images come from GHCR (pushed by `.github/workflows/deploy.yml` on every push to
`main`). On the deploy host:

```bash
sudo mkdir -p /opt/ai-edge-ops && cd /opt/ai-edge-ops
# CI scp's docker-compose.prod.yml + Caddyfile + mediamtx.prod.yml here each deploy
cp .env.prod.example .env        # DOMAIN, POSTGRES_PASSWORD, JWT_SECRET, MINIO_ROOT_*
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Full runbook — TLS, MQTT mTLS, schema, secrets, rollback, backups — in
[`DEPLOY.md`](DEPLOY.md). Running an edge device against a production broker:
[`backend/edge_agent/README.md`](backend/edge_agent/README.md).

---

## Test

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -e "packages/svc_core[fastapi,mqtt,dev]" \
                          -e "libs/edge_protocol[dev]" \
                          -e "server[dev]" -e "edge_agent[dev]"

for pkg in packages/svc_core libs/edge_protocol server edge_agent; do
  (cd "$pkg" && python -m pytest -q)
done
```
