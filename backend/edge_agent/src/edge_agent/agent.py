"""Agent orchestrator: owns state + runtime, executes commands, reconciles."""

from __future__ import annotations

import datetime as dt
import logging

import edge_protocol as p
from dqh.svc_core.messaging import Envelope

from edge_agent.artifacts import fetch_artifact
from edge_agent.config import AgentSettings
from edge_agent.link import EdgeLink
from edge_agent.runtime import InferenceRuntime
from edge_agent.state import StateStore

logger = logging.getLogger("edge_agent")


class Agent:
    def __init__(
        self,
        settings: AgentSettings,
        *,
        runtime: InferenceRuntime,
        store: StateStore,
        link: EdgeLink | None = None,
    ) -> None:
        self.settings = settings
        self.runtime = runtime
        self.store = store
        self.link: EdgeLink | None = link

    # --- command handling (called by EdgeLink) ------------------------
    async def handle_command(self, env: Envelope) -> p.CommandAckPayload:
        if env.type == p.T_DEPLOY_MODEL:
            return await self._deploy(p.DeployModelPayload.model_validate(env.payload))
        if env.type == p.T_UPDATE_CONFIG:
            return await self._update_config(p.UpdateConfigPayload.model_validate(env.payload))
        if env.type == p.T_RESTART:
            return p.CommandAckPayload(command_id=env.id, status="succeeded", detail="restart noop")
        if env.type == p.T_RUN_DIAGNOSTICS:
            return p.CommandAckPayload(
                command_id=env.id, status="succeeded", detail=self._diagnostics()
            )
        return p.CommandAckPayload(command_id=env.id, status="failed", detail="unknown command")

    async def _deploy(self, cmd: p.DeployModelPayload) -> p.CommandAckPayload:
        st = self.store.state
        st.desired.deployment_id = cmd.deployment_id
        st.desired.model_version_id = cmd.model_version_id
        st.desired.artifact_uri = cmd.artifact_uri
        st.desired.model_format = cmd.format
        st.desired.config = cmd.config
        st.reported.runtime_status = "applying"
        st.reported.deployment_id = cmd.deployment_id
        self.store.save()
        await self._report_state()

        try:
            path = await fetch_artifact(
                cmd.artifact_uri,
                dest_dir=self.settings.inference.weights_dir,
                filename=f"mv-{cmd.model_version_id}.{cmd.format}",
                checksum_sha256=cmd.checksum_sha256,
            )
            await self.runtime.load(
                weights_path=path,
                model_version_id=cmd.model_version_id,
                config={**self.settings.inference.model_dump(), **cmd.config},
            )
        except Exception as exc:  # noqa: BLE001
            st.reported.runtime_status = "failed"
            st.reported.detail = str(exc)
            self.store.save()
            await self._report_state()
            return p.CommandAckPayload(
                command_id=cmd.command_id, deployment_id=cmd.deployment_id,
                status="failed", detail=str(exc),
            )

        st.reported.runtime_status = "active"
        st.reported.active_model_version_id = cmd.model_version_id
        st.reported.detail = None
        self.store.save()
        await self._report_state()
        return p.CommandAckPayload(
            command_id=cmd.command_id, deployment_id=cmd.deployment_id, status="succeeded"
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
        if st.in_sync():
            return
        if st.desired.artifact_uri and st.desired.model_version_id != self.runtime.model_version_id:
            logger.info("reconcile: re-applying desired model %s", st.desired.model_version_id)
            await self._deploy(
                p.DeployModelPayload(
                    command_id="reconcile",
                    deployment_id=st.desired.deployment_id or 0,
                    model_version_id=st.desired.model_version_id,
                    artifact_uri=st.desired.artifact_uri,
                    format=st.desired.model_format or "pt",
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
                active_model_version_id=r.active_model_version_id,
                deployment_id=r.deployment_id,
                runtime_status=r.runtime_status,
                config=r.config,
                detail=r.detail,
            )
        )

    def _diagnostics(self) -> str:
        return (
            f"runtime={self.store.state.reported.runtime_status} "
            f"model={self.runtime.model_version_id} "
            f"loaded={self.runtime.loaded} at {dt.datetime.now(tz=dt.timezone.utc).isoformat()}"
        )
