"""Agent orchestrator: owns state + runtime, executes commands, reconciles."""

from __future__ import annotations

import datetime as dt
import logging

import edge_protocol as p
from dqh.svc_core.messaging import Envelope

from edge_agent.core.config import AgentSettings
from edge_agent.core.state import StateStore
from edge_agent.network.link import EdgeLink
from edge_agent.runner import ComposeRunner, ModelDeployer
from edge_agent.runtime import InferenceRuntime
from edge_agent.services.artifacts import fetch_artifact

logger = logging.getLogger("edge_agent")


class Agent:
    def __init__(
        self,
        settings: AgentSettings,
        *,
        runtime: InferenceRuntime,
        store: StateStore,
        link: EdgeLink | None = None,
        deployer: ModelDeployer | None = None,
    ) -> None:
        self.settings = settings
        self.runtime = runtime
        self.store = store
        self.link: EdgeLink | None = link
        # image-based deploy (new). The legacy artifact path uses `runtime`.
        self.deployer: ModelDeployer = deployer or ComposeRunner(settings.compose)

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
        st = self.store.state
        st.desired.deployment_id = cmd.deployment_id
        st.desired.model_version_id = cmd.model_version_id
        st.desired.image = cmd.image
        st.desired.artifact_uri = cmd.artifact_uri
        st.desired.model_format = cmd.format
        st.desired.config = cmd.config
        effective_config = {**self.settings.inference.model_dump(), **cmd.config}
        st.reported.config = effective_config
        st.reported.runtime_status = "applying"
        st.reported.deployment_id = cmd.deployment_id
        self.store.save()
        await self._report_state()

        try:
            if cmd.image:
                detail = await self._apply_image(cmd.image)
            else:
                detail = await self._apply_artifact(cmd, effective_config)
        except Exception as exc:  # noqa: BLE001
            st.reported.runtime_status = "failed"
            st.reported.detail = str(exc)
            self.store.save()
            await self._report_state()
            return p.CommandAckPayload(
                command_id=cmd.command_id, deployment_id=cmd.deployment_id,
                status="failed", detail=str(exc),
            )

        if detail is not None:  # non-None detail == failure reason
            st.reported.runtime_status = "failed"
            st.reported.detail = detail
            self.store.save()
            await self._report_state()
            return p.CommandAckPayload(
                command_id=cmd.command_id, deployment_id=cmd.deployment_id,
                status="failed", detail=detail,
            )

        st.reported.runtime_status = "active"
        st.reported.active_model_version_id = cmd.model_version_id
        st.reported.detail = None
        self.store.save()
        await self._report_state()
        return p.CommandAckPayload(
            command_id=cmd.command_id, deployment_id=cmd.deployment_id, status="succeeded"
        )

    async def _apply_image(self, image: str) -> str | None:
        """Pull + run the model image via compose. Returns a failure reason or None."""
        result = await self.deployer.deploy(image)
        return None if result.ok else result.detail

    async def _apply_artifact(self, cmd: p.DeployModelPayload, config: dict) -> str | None:
        """Legacy path: download the artifact and load it into the local runtime."""
        path = await fetch_artifact(
            cmd.artifact_uri,
            dest_dir=self.settings.inference.weights_dir,
            filename=f"mv-{cmd.model_version_id}.{cmd.format or 'pt'}",
            checksum_sha256=cmd.checksum_sha256,
        )
        await self.runtime.load(
            weights_path=path, model_version_id=cmd.model_version_id, config=config
        )
        return None

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
        if not (st.desired.image or st.desired.artifact_uri):
            return
        if st.reported.runtime_status == "applying":
            return  # a deploy is in flight
        logger.info("reconcile: re-applying desired model %s", st.desired.model_version_id)
        await self._deploy(
            p.DeployModelPayload(
                command_id="reconcile",
                deployment_id=st.desired.deployment_id or 0,
                model_version_id=st.desired.model_version_id or 0,
                image=st.desired.image,
                artifact_uri=st.desired.artifact_uri,
                format=st.desired.model_format,
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
