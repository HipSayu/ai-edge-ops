"""Agent orchestrator: owns desired/reported state, executes commands, reconciles.

Inference runs in the vision-runtime container; the agent only deploys the model
image (via ``docker compose``) and reports the outcome.
"""

from __future__ import annotations

import datetime as dt
import logging

import edge_protocol as p
from dqh.svc_core.messaging import Envelope

from edge_agent.core.config import AgentSettings
from edge_agent.core.state import StateStore
from edge_agent.network.link import EdgeLink
from edge_agent.runner import ComposeRunner, ModelDeployer

logger = logging.getLogger("edge_agent")


class Agent:
    def __init__(
        self,
        settings: AgentSettings,
        *,
        store: StateStore,
        link: EdgeLink | None = None,
        deployer: ModelDeployer | None = None,
    ) -> None:
        self.settings = settings
        self.store = store
        self.link: EdgeLink | None = link
        self.deployer: ModelDeployer = deployer or ComposeRunner(settings.compose)
        self.inference = None  # set by main.run(): the InferenceClient, for the status API

    # --- command handling (called by EdgeLink) ------------------------
    async def handle_command(self, env: Envelope) -> p.CommandAckPayload:
        if env.type == p.T_DEPLOY_MODEL:
            return await self._deploy(p.DeployModelPayload.model_validate(env.payload))
        if env.type == p.T_UPDATE_CONFIG:
            return await self._update_config(p.UpdateConfigPayload.model_validate(env.payload))
        if env.type == p.T_RESTART:
            result = await self.deployer.restart()
            return p.CommandAckPayload(
                command_id=env.id,
                status="succeeded" if result.ok else "failed",
                detail=result.detail or "inference service restarted",
            )
        if env.type == p.T_RUN_DIAGNOSTICS:
            return p.CommandAckPayload(
                command_id=env.id, status="succeeded", detail=self._diagnostics()
            )
        return p.CommandAckPayload(command_id=env.id, status="failed", detail="unknown command")

    async def _deploy(self, cmd: p.DeployModelPayload) -> p.CommandAckPayload:
        if not cmd.image:
            return p.CommandAckPayload(
                command_id=cmd.command_id,
                deployment_id=cmd.deployment_id,
                status="failed",
                detail="deploy command has no image (this agent is image-only)",
            )
        st = self.store.state
        st.desired.deployment_id = cmd.deployment_id
        st.desired.image = cmd.image
        st.desired.config = cmd.config
        st.reported.config = cmd.config
        st.reported.runtime_status = "applying"
        st.reported.deployment_id = cmd.deployment_id
        self.store.save()
        await self._report_state()

        try:
            result = await self.deployer.deploy(cmd.image)
        except Exception as exc:  # noqa: BLE001
            return await self._fail(cmd, str(exc))
        if not result.ok:
            return await self._fail(cmd, result.detail)

        st.reported.runtime_status = "active"
        st.reported.active_image = cmd.image
        st.reported.detail = None
        self.store.save()
        await self._report_state()
        return p.CommandAckPayload(
            command_id=cmd.command_id, deployment_id=cmd.deployment_id, status="succeeded"
        )

    async def _fail(self, cmd: p.DeployModelPayload, detail: str) -> p.CommandAckPayload:
        st = self.store.state
        st.reported.runtime_status = "failed"
        st.reported.detail = detail
        self.store.save()
        await self._report_state()
        return p.CommandAckPayload(
            command_id=cmd.command_id,
            deployment_id=cmd.deployment_id,
            status="failed",
            detail=detail,
        )

    async def _update_config(self, cmd: p.UpdateConfigPayload) -> p.CommandAckPayload:
        self.store.state.desired.config.update(cmd.config)
        self.store.state.reported.config.update(cmd.config)
        self.store.save()
        await self._report_state()
        return p.CommandAckPayload(
            command_id=cmd.command_id, deployment_id=cmd.deployment_id, status="succeeded"
        )

    # --- reconcile (periodic) ---------------------------------------
    async def reconcile(self) -> None:
        st = self.store.state
        if st.in_sync() or not st.desired.image:
            return
        if st.reported.runtime_status == "applying":
            return  # a deploy is in flight
        if self.deployer.current_image() == st.desired.image:
            return  # image already running; nothing to re-pull
        logger.info("reconcile: re-applying desired image %s", st.desired.image)
        await self._deploy(
            p.DeployModelPayload(
                command_id="reconcile",
                deployment_id=st.desired.deployment_id or 0,
                image=st.desired.image,
                config=st.desired.config,
            )
        )

    # --- state report ----------------------------------------------
    async def _report_state(self) -> None:
        if self.link is None:
            return
        r = self.store.state.reported
        await self.link.send_state(
            p.StateReportPayload(
                active_image=r.active_image,
                deployment_id=r.deployment_id,
                runtime_status=r.runtime_status,
                config=r.config,
                detail=r.detail,
            )
        )

    def _diagnostics(self) -> str:
        r = self.store.state.reported
        return (
            f"runtime_status={r.runtime_status} "
            f"image={self.deployer.current_image()} "
            f"at {dt.datetime.now(tz=dt.timezone.utc).isoformat()}"
        )
