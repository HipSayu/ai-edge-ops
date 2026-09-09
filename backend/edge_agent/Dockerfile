# Build context = backend/ (see edge_agent/compose.yml).
# The agent is the host supervisor: MQTT link, control/reconcile, telemetry, and
# it drives `docker compose` to deploy the model image as the `inference` service
# — so it needs the docker CLI + compose plugin and the docker socket mounted.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    STATE_FILE=/var/lib/edge-agent/state.json \
    COMPOSE__PROJECT_DIR=/project

RUN apt-get update && apt-get install -y --no-install-recommends \
        docker.io docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
COPY packages/svc_core /srv/packages/svc_core
COPY libs/edge_protocol /srv/libs/edge_protocol
COPY edge_agent /srv/edge_agent

RUN pip install --upgrade pip \
 && pip install -e "/srv/packages/svc_core[mqtt]" \
 && pip install -e "/srv/libs/edge_protocol" \
 && pip install -e "/srv/edge_agent" \
 && mkdir -p /var/lib/edge-agent

EXPOSE 9100
CMD ["edge-agent"]
