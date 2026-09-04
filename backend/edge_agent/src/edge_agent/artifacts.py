"""Fetch a model artifact referenced by a DeployModel command."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import httpx

logger = logging.getLogger("edge_agent.artifacts")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


async def fetch_artifact(
    artifact_uri: str,
    *,
    dest_dir: str,
    filename: str,
    checksum_sha256: str | None = None,
    timeout_s: float = 120.0,
) -> str:
    """Download ``artifact_uri`` (presigned https URL) to ``dest_dir/filename``.

    Returns the local path. Raises on checksum mismatch.
    """
    if not artifact_uri.startswith(("http://", "https://")):
        raise ValueError(f"unsupported artifact scheme: {artifact_uri!r} (need a presigned URL)")

    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / filename
    tmp = target.with_suffix(target.suffix + ".part")

    async with (
        httpx.AsyncClient(timeout=timeout_s) as client,
        client.stream("GET", artifact_uri) as resp,
    ):
        resp.raise_for_status()
        with tmp.open("wb") as fh:
            async for chunk in resp.aiter_bytes():
                fh.write(chunk)

    if checksum_sha256 and _sha256(tmp) != checksum_sha256:
        tmp.unlink(missing_ok=True)
        raise ValueError("artifact checksum mismatch")

    tmp.replace(target)
    logger.info("fetched artifact -> %s", target)
    return str(target)
