# Build context = repo root (see .github/workflows/deploy.yml and deploy/compose.app.yml).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

COPY packages/svc_core /srv/packages/svc_core
COPY packages/ai_core /srv/packages/ai_core
COPY libs/edge_protocol /srv/libs/edge_protocol
COPY server /srv/server

RUN pip install --upgrade pip \
 && pip install -e "/srv/packages/svc_core[fastapi,mqtt,redis,sqlalchemy,security,httpclient]" \
 && pip install -e "/srv/packages/ai_core[mcp,openai]" \
 && pip install -e "/srv/libs/edge_protocol" \
 && pip install -e "/srv/server[dev]"

WORKDIR /srv/server
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
