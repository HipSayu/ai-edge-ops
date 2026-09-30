#!/usr/bin/env bash
# One-off: move the cloud stack on the EC2 host from k3s to docker compose.
# Run ON the server from the copied repo root (needs infra/compose/cloud/{.env,assistant.env} filled in):
#   bash infra/scripts/migrate-k3s-to-compose.sh
set -euo pipefail

BACKUP=/home/ec2-user/pg-backup-$(date +%Y%m%d-%H%M).sql
KUBECTL="sudo k3s kubectl -n edgeops-cloud"

echo "== 1. Backup Postgres from k3s -> $BACKUP"
$KUBECTL exec postgres-0 -- sh -c 'pg_dumpall -U "$POSTGRES_USER"' > "$BACKUP"
ls -lh "$BACKUP"

echo "== 2. Stop k3s (frees RAM and port 80; uninstall later with k3s-uninstall.sh)"
sudo /usr/local/bin/k3s-killall.sh
sudo systemctl disable --now k3s

echo "== 3. Start the compose stack"
cd infra/compose/cloud
docker compose up -d --build postgres redis mqtt
until docker compose exec -T postgres pg_isready >/dev/null 2>&1; do sleep 2; done

echo "== 4. Restore Postgres"
docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d postgres' < "$BACKUP"

docker compose up -d --build api assistant dashboard
docker compose ps

echo "== 5. Smoke checks"
sleep 20
curl -fsS http://127.0.0.1/api/v1/health >/dev/null && echo "dashboard -> api OK" || echo "dashboard -> api FAIL"
docker compose logs assistant | grep -E "agent tools bound|ERROR" | tail -5
