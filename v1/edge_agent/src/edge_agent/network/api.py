"""Local HTTP API — for a field technician / on-device UI / probes."""

from __future__ import annotations

from dqh.svc_core.transports.http import ok
from dqh.svc_core.transports.http.fastapi import create_app
from fastapi import APIRouter, FastAPI, Request

from edge_agent.services.agent import Agent

router = APIRouter(tags=["agent"])


def _agent(request: Request) -> Agent:
    return request.app.state.agent


@router.get("/status")
async def status(request: Request):
    agent = _agent(request)
    st = agent.store.state
    inference = agent.inference
    return ok(
        {
            "device_id": agent.settings.device_id,
            "runtime_status": st.reported.runtime_status,
            "active_image": st.reported.active_image,
            "desired_image": st.desired.image,
            "in_sync": st.in_sync(),
            "inference_connected": bool(inference and inference.connected),
            "inference_health": (
                inference.last_health.model_dump()
                if inference and inference.last_health
                else None
            ),
            "cameras": [c.id for c in agent.settings.cameras],
        }
    )


@router.get("/config")
async def get_config(request: Request):
    return ok(_agent(request).store.state.reported.config)


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
        title="edge",
        routers=[router],
        router_prefix="",
        health_path="/health",
    )
    app.state.agent = agent
    return app
