# AI Edge Ops — Backend

FastAPI service for the edge AI operations platform.

```
ai-edge-ops
├── fleet          devices + monitoring telemetry (heartbeats, metrics)
├── model_registry models + versioned / compressed artifacts
├── deployment     bind a published model version to a device
└── observability  violations · alerts · analytics
```

## Architecture

Modular monolith, **package-by-feature**. One module per bounded context under
`app/modules/<name>/`, each with a fixed layout:

| File | Responsibility |
|------|----------------|
| `router.py`     | HTTP layer — request/response, status codes. No logic. |
| `service.py`    | Use-cases, transaction boundary, publishes events. **No FastAPI imports.** |
| `repository.py` | All query construction. Flushes but never commits. |
| `models.py`     | SQLAlchemy ORM. |
| `schemas.py`    | Pydantic request/response contracts. |
| `domain.py`     | Enums, events, pure business rules. |
| `events.py`     | Subscribers to other modules' events. |

Modules talk to each other only via **public services** (exported from the module
`__init__.py`) or **domain events** (`app/core/events.py`) — never by importing
another module's repository or models.

Request flow: `router → service → repository → model`.

## Run

```bash
# from repo root — full stack (Postgres + backend + frontend)
docker compose up --build
#   API docs:  http://localhost:8000/docs
#   frontend:  http://localhost:5173

# or backend only, locally
cd backend
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Schema is created on startup (`init_db` → `Base.metadata.create_all`). Swap for
Alembic migrations when the schema stabilises.

## Test

```bash
cd backend
.venv/bin/pytest          # in-memory SQLite, no external services
```

## Config

Environment variables (see `.env.example`): `DATABASE_URL`, `CORS_ORIGINS`,
`OFFLINE_THRESHOLD_SECONDS`, `LATENCY_SLO_MS`.
