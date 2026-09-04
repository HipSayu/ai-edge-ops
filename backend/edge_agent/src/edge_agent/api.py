"""Local HTTP API — for a field technician / on-device UI / probes."""

from __future__ import annotations

from dqh.svc_core.http import ok
from dqh.svc_core.http.adapters.fastapi import create_app
from fastapi import APIRouter, FastAPI, Request

from edge_agent.agent import Agent

router = APIRouter(tags=["agent"])


def _agent(request: Request) -> Agent:
    return request.app.state.agent


@router.get("/status")
async def status(request: Request):
    agent = _agent(request)
    st = agent.store.state
    return ok(
        {
            "device_id": agent.settings.device_id,
            "runtime_status": st.reported.runtime_status,
            "active_model_version_id": st.reported.active_model_version_id,
            "desired_model_version_id": st.desired.model_version_id,
            "in_sync": st.in_sync(),
            "runtime_loaded": agent.runtime.loaded,
            "cameras": [c.id for c in agent.settings.cameras],
        }
    )


@router.get("/config")
async def get_config(request: Request):
    return ok(_agent(request).settings.inference.model_dump())


@router.put("/config")
async def put_config(request: Request, patch: dict):
    agent = _agent(request)
    agent.store.state.desired.config.update(patch)
    agent.store.save()
    return ok(agent.store.state.desired.config)


@router.get("/cameras")
async def cameras(request: Request):
    return ok([c.model_dump() for c in _agent(request).settings.cameras])


@router.post("/model/reconcile")
async def reconcile(request: Request):
    await _agent(request).reconcile()
    return ok({"in_sync": _agent(request).store.state.in_sync()})


def build_api(agent: Agent) -> FastAPI:
    app = create_app(
        title="edge-agent",
        routers=[router],
        router_prefix="",
        health_path="/health",
    )
    app.state.agent = agent
    return app
