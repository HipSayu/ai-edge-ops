"""Deploy a model by swapping the ``inference`` compose service's image.

`deploy(image)`:
  1. remember the current ``INFERENCE_IMAGE`` (last-known-good)
  2. write the new digest-pinned ref into the env file
  3. ``docker compose pull inference``
  4. ``docker compose up -d --wait inference``  (blocks on the container healthcheck)
  5. on any failure -> restore the env file, bring the old image back up, report failed
  6. on success   -> prune images older than the last-known-good

The agent never loads a model itself; the model image (built by CI, one per edge
backend variant) carries the weights + runtime.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from edge_agent.core.config import ComposeConfig

logger = logging.getLogger("edge_agent.runner.compose")


@dataclass(frozen=True)
class DeployResult:
    ok: bool
    detail: str = ""


class ModelDeployer(Protocol):
    async def deploy(self, image: str) -> DeployResult: ...
    async def restart(self) -> DeployResult: ...
    def current_image(self) -> str | None: ...


class ComposeRunner:
    def __init__(self, config: ComposeConfig) -> None:
        self._cfg = config
        self._env_path = Path(config.env_file)

    # --- public -------------------------------------------------------
    def current_image(self) -> str | None:
        return self._read_env().get(self._cfg.image_var)

    async def deploy(self, image: str) -> DeployResult:
        previous = self.current_image()
        if image == previous:
            return DeployResult(True, "already running this image")

        self._set_env(self._cfg.image_var, image)
        rc, out = await self._compose("pull", self._cfg.service)
        if rc != 0:
            self._restore(previous)
            return DeployResult(False, f"pull failed: {out.strip()[-500:]}")

        rc, out = await self._compose("up", "-d", "--wait", self._cfg.service)
        if rc != 0:
            self._restore(previous)
            await self._compose("up", "-d", self._cfg.service)
            return DeployResult(False, f"up failed: {out.strip()[-500:]}")

        await self._prune(keep=previous)
        return DeployResult(True)

    async def restart(self) -> DeployResult:
        rc, out = await self._compose("restart", self._cfg.service)
        return DeployResult(rc == 0, "" if rc == 0 else out.strip()[-500:])

    # --- internals ---------------------------------------------------
    def _restore(self, previous: str | None) -> None:
        if previous is None:
            self._unset_env(self._cfg.image_var)
        else:
            self._set_env(self._cfg.image_var, previous)

    async def _compose(self, *args: str) -> tuple[int, str]:
        cmd = ["docker", "compose", "--env-file", str(self._env_path), *args]
        logger.info("run: %s", " ".join(cmd))
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self._cfg.project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=self._cfg.up_timeout_s)
        except TimeoutError:
            proc.kill()
            return 124, f"timed out after {self._cfg.up_timeout_s}s"
        return proc.returncode or 0, out.decode(errors="replace")

    async def _prune(self, *, keep: str | None) -> None:
        """Best-effort: drop dangling images. The current image and ``keep``
        (last-known-good, still referenced by the env file's history) survive
        because they are tagged/in-use; only untagged layers go."""
        if self._cfg.keep_previous_images < 0:
            return
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker",
                "image",
                "prune",
                "-f",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
        except Exception:  # noqa: BLE001 - prune is best-effort
            logger.warning("image prune failed", exc_info=True)

    # --- env file --------------------------------------------------
    def _read_env(self) -> dict[str, str]:
        if not self._env_path.exists():
            return {}
        out: dict[str, str] = {}
        for line in self._env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
        return out

    def _write_env(self, values: dict[str, str]) -> None:
        self._env_path.parent.mkdir(parents=True, exist_ok=True)
        body = "".join(f"{k}={v}\n" for k, v in values.items())
        self._env_path.write_text(body)

    def _set_env(self, key: str, value: str) -> None:
        values = self._read_env()
        values[key] = value
        self._write_env(values)

    def _unset_env(self, key: str) -> None:
        values = self._read_env()
        values.pop(key, None)
        self._write_env(values)


__all__ = ["ComposeRunner", "DeployResult", "ModelDeployer"]
