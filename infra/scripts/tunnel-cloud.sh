#!/usr/bin/env bash
# Forward the cloud compose infra on EC2 to localhost so apps run locally with .env.local:
#   Postgres 127.0.0.1:15432, Redis 127.0.0.1:16379, MQTT 127.0.0.1:11883
# Keep it running; Ctrl+C to close.
#   bash infra/scripts/tunnel-cloud.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
KEY="${SSH_KEY:-$ROOT/cert/huce.pem}"
HOST="${SSH_HOST:-ec2-user@ec2-18-207-125-238.compute-1.amazonaws.com}"
PROJECT=edgeops-cloud
chmod 600 "$KEY" 2>/dev/null || true

# Containers are only on the compose network (reachable from the host); look their IPs up on each start.
ip() {
  ssh -i "$KEY" "$HOST" "sudo docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $PROJECT-$1-1" | tr -d '\r'
}
PG=$(ip postgres)
REDIS=$(ip redis)
MQTT=$(ip mqtt)
echo "Tunnel -> $HOST: Postgres $PG:5432 -> 15432, Redis $REDIS:6379 -> 16379, MQTT $MQTT:1883 -> 11883"

exec ssh -i "$KEY" -N \
  -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -L "15432:$PG:5432" \
  -L "16379:$REDIS:6379" \
  -L "11883:$MQTT:1883" \
  "$HOST"
