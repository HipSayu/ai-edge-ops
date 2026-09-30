#!/usr/bin/env bash
# Run N simulated edge nodes on this host, next to the edgeops-cloud compose stack (they join its network).
# Node identities come from infra/compose/edge-sim/sim-<i>.env (written by infra/scripts/seed_demo.py).
#
#   infra/scripts/edge-sim.sh 4          # start sims 1..4
#   infra/scripts/edge-sim.sh 4 down     # remove them
set -euo pipefail

COUNT=${1:?usage: edge-sim.sh <count> [down]}
ACTION=${2:-up}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
DIR=$ROOT/infra/compose/edge-sim
EXPORTER=edgeops-sim-exporter

# Shared host metrics for all sims, on the cloud network only (nothing published on the host)
if [ "$ACTION" != down ] && ! docker inspect "$EXPORTER" >/dev/null 2>&1; then
  docker run -d --name "$EXPORTER" --restart unless-stopped --network edgeops-cloud_default --pid host \
    -v /:/host:ro,rslave prom/node-exporter:v1.8.2 \
    --path.rootfs=/host --path.procfs=/host/proc --path.sysfs=/host/sys --web.listen-address=:9100
fi

for i in $(seq 1 "$COUNT"); do
  export SIM_ENV=$DIR/sim-$i.env SIM_STATE=/var/lib/edgeops-sim-$i
  if [ "$ACTION" = down ]; then
    docker compose -p "edgeops-sim-$i" -f "$DIR/docker-compose.yml" down
    # Runtimes the sim started are its own containers, not part of the compose project
    docker ps -aq --filter "label=edgeops.node_id=$(sed -n 's/^EDGE_NODE_ID=//p' "$SIM_ENV")" | xargs -r docker rm -f
    continue
  fi
  [ -f "$SIM_ENV" ] || { echo "missing $SIM_ENV (run seed_demo.py first)" >&2; exit 1; }
  docker compose -p "edgeops-sim-$i" -f "$DIR/docker-compose.yml" up -d
done

[ "$ACTION" = down ] && { docker rm -f "$EXPORTER" >/dev/null 2>&1 || true; exit 0; }
docker ps --filter "name=edgeops-sim" --format 'table {{.Names}}\t{{.Status}}'
