# Production deploy

CI/CD deploys **frontend + server only**. `edge_agent` ships as a separate image
that operators pull onto each device (see `docs/run-edge-agent.md`).

```
GitHub push to main
   ├─ CI (.github/workflows/ci.yml)        lint + tests (all packages + frontend)
   └─ Deploy (.github/workflows/deploy.yml)
        ├─ build ghcr.io/<owner>/ai-edge-ops-server:<sha>   (context: backend/, needs the submodule)
        ├─ build ghcr.io/<owner>/ai-edge-ops-frontend:<sha> (context: frontend/, nginx SPA)
        └─ ssh to $DEPLOY_HOST → scp deploy/compose.infra.yml + compose.app.yml +
           config/ to /opt/ai-edge-ops, then docker compose pull && up -d
```

The prod stack is the infra base (`compose.infra.yml`) **plus** the app overlay
(`compose.app.yml` — Caddy + frontend + server). Caddy terminates TLS and routes
`/api/*` → `server:8000`, `/*/whip|whep` → `mediamtx:8889`, everything else →
`frontend:80`.

## One-time host setup

```bash
sudo mkdir -p /opt/ai-edge-ops && cd /opt/ai-edge-ops
# CI scp's compose.infra.yml + compose.app.yml + config/ here on every deploy.
# Copy the env templates once (from app/deploy/ in the repo):
cp .env.infra.example .env.infra
cp .env.app.example   .env.app
$EDITOR .env.infra .env.app    # POSTGRES_PASSWORD, EMQX_DASHBOARD_PASSWORD,
                               # REDIS_PASSWORD, JWT_SECRET, DOMAIN, MQTT_USERNAME/PASSWORD,
                               # SERVER_ENVIRONMENT=production, SERVER_MQTT_TLS=true,
                               # SERVER_MQTT_PORT=8883, SERVER_CORS_ORIGINS=["https://$DOMAIN"],
                               # SERVER_MEDIAMTX_WHEP_URL=https://$DOMAIN, MEDIAMTX_WEBRTC_HOST=$DOMAIN
export COMPOSE_FILE=compose.infra.yml:compose.app.yml
export COMPOSE_ENV_FILES=.env.infra,.env.app
docker compose up -d
```

Apply the reference schema after the database is healthy:

```bash
docker compose exec -T db psql -U ppe -d ai_edge_ops < /opt/ai-edge-ops/schema.sql
```

Run this explicitly for every schema release. The server's `init_db()` is only
intended for local/test startup and does not alter existing tables.

DNS: point `DOMAIN` A/AAAA at the host. Open `80`, `443`, and the MQTT-TLS port
(`MQTT_TLS_PORT`, default `58883`). Keep the Postgres / Redis / EMQX-dashboard
host ports closed to the internet.

### MQTT mTLS and per-device ACL

The server and each edge device connect to MQTT over TLS on port `8883`.
Mount the certificates read-only using this layout:

```text
server secrets/server-mqtt/: ca.crt, server.crt, server.key
edge   certs/:              ca.crt, client.crt, client.key
```

Issue a unique client certificate for every `DEVICE_ID`. Configure EMQX ACLs so
each device can subscribe only to `agent/devices/{device_id}/cmd` and publish
only to its own `state`, `events`, `telemetry`, and `ack` topics. Do not share
one client certificate across devices.

## GitHub secrets / variables

Repo **Settings → Secrets and variables → Actions**:

| Secret | Used for |
|---|---|
| `SUBMODULE_PAT` | classic PAT with `repo` scope — CI checks out the private `python-packages` submodule |
| `DEPLOY_HOST` | deploy host IP / DNS |
| `DEPLOY_USER` | ssh user (in the `docker` group) |
| `DEPLOY_SSH_KEY` | private key for that user; add the public key to the host's `authorized_keys` |

`GITHUB_TOKEN` (automatic) pushes images to GHCR and logs the host into GHCR.
Add an **Environment** named `production` (Settings → Environments) for the deploy
job — optionally with a required-reviewer gate.

Make the GHCR packages readable by the deploy host: either the host logs in with a
PAT, or set the `ai-edge-ops-server` / `-frontend` packages' visibility so the
`GITHUB_TOKEN` login in the deploy step can pull them.

## Rollback

```bash
cd /opt/ai-edge-ops
sed -i 's/^IMAGE_TAG=.*/IMAGE_TAG=<previous-sha>/' .env.app
docker compose pull && docker compose up -d      # COMPOSE_FILE / COMPOSE_ENV_FILES from your shell rc
```

## Backups

```bash
# cron, daily
docker compose exec -T db pg_dump -U ppe ai_edge_ops | gzip > /backups/aeo-$(date +%F).sql.gz
```
