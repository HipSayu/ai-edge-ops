import hashlib
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import httpx

from src.shared.exceptions import AppException, ErrorCode

logger = logging.getLogger(__name__)


class HttpArtifactFetcher:
    """Downloads artifacts from HTTP(S) URLs (e.g. presigned Object Storage URLs) into a local cache.

    `file://` URIs and plain paths are used in place. Files are cached by URL hash so redeploys are cheap.
    """

    def __init__(self, cache_dir: str, timeout_sec: float = 300.0) -> None:
        self._cache = Path(cache_dir)
        self._timeout = timeout_sec

    async def fetch(self, uri: str) -> str:
        parsed = urlparse(uri)
        if parsed.scheme in ("", "file") or (len(parsed.scheme) == 1 and os.name == "nt"):
            path = Path(parsed.path if parsed.scheme == "file" else uri)
            if not path.exists():
                raise AppException(ErrorCode.NOT_FOUND, f"Artifact not found: {path}")
            return str(path.resolve())
        if parsed.scheme not in ("http", "https"):
            raise AppException(
                ErrorCode.INVALID_REQUEST, f"Unsupported artifact scheme '{parsed.scheme}' (use a presigned https URL)"
            )

        name = Path(parsed.path).name or "artifact"
        target = self._cache / hashlib.sha256(uri.split("?")[0].encode()).hexdigest()[:16] / name
        if target.exists():
            return str(target.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".part")
        logger.info("Downloading artifact %s", name)
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            async with client.stream("GET", uri) as response:
                response.raise_for_status()
                with tmp.open("wb") as fh:
                    async for chunk in response.aiter_bytes(1 << 20):
                        fh.write(chunk)
        os.replace(tmp, target)
        return str(target.resolve())
