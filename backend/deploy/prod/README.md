# Production deploy

CI/CD deploys **frontend + server only**. `edge_agent` ships as a separate image
that operators pull onto each device (see `docs/run-edge-agent.md`).

```
GitHub push to main
   ├─ CI (.github/workflows/ci.yml)        lint + tests (all packages + frontend)
   └─ Deploy (.github/workflows/deploy.yml)
        ├─ build ghcr.io/<owner>/ai-edge-ops-server:<sha>   (context: backend/, needs the submodule)
        ├─ build ghcr.io/<owner>/ai-edge-ops-frontend:<sha> (context: frontend/, nginx SPA)
        └─ ssh to $DEPLOY_HOST → docker compose pull && up -d   (this folder's compose)
```

Caddy terminates TLS and routes `/api/*` → `server:8000`, everything else →
`frontend:80`.

## One-time host setup

```bash
sudo mkdir -p /opt/ai-edge-ops && cd /opt/ai-edge-ops
# put docker-compose.yml + Caddyfile here (CI scp's them on every deploy, or copy once)
cp .env.example .env         # from backend/deploy/prod/
$EDITOR .env                  # DOMAIN, POSTGRES_PASSWORD, MINIO_ROOT_*
docker compose up -d
```

DNS: point `DOMAIN` A/AAAA at the host. Open `80`, `443`, and `8883` (MQTT TLS for
edge devices). Keep `5432`/`6379`/`9000`/`18083` closed to the internet.

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
sed -i 's/^IMAGE_TAG=.*/IMAGE_TAG=<previous-sha>/' .env
docker compose pull && docker compose up -d
```

## Backups

```bash
# cron, daily
docker compose exec -T db pg_dump -U ppe ai_edge_ops | gzip > /backups/aeo-$(date +%F).sql.gz
```
