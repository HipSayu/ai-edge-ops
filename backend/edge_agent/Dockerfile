# Build context = backend/ (see edge_agent/compose.yml).
# x86 dev/demo image. For Jetson, swap the base for an l4t-pytorch image and
# install the [inference] extra.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    STATE_FILE=/var/lib/edge-agent/state.json \
    INFERENCE__WEIGHTS_DIR=/var/lib/edge-agent/models

WORKDIR /srv

COPY packages/svc_core /srv/packages/svc_core
COPY libs/edge_protocol /srv/libs/edge_protocol
COPY edge_agent /srv/edge_agent

RUN pip install --upgrade pip \
 && pip install -e "/srv/packages/svc_core[mqtt]" \
 && pip install -e "/srv/libs/edge_protocol" \
 && pip install -e "/srv/edge_agent" \
 && mkdir -p /var/lib/edge-agent/models

EXPOSE 9100
CMD ["edge-agent"]
