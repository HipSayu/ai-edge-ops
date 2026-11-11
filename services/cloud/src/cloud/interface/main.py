"""The cloud interface: REST at /api/v1 (and /api), MCP tools at /mcp. Everything is declared in app.py.

Run from `app/`: `uvicorn cloud.interface.main:app --port 8100`."""

from cloud.interface.rest.app import create_app
from trace_id import configure_logging

configure_logging("cloud")
app = create_app()
