"""Upload selected inference evidence frames to the control plane."""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Protocol

from dqh.svc_core.transports.http.client import HttpClient

logger = logging.getLogger("vision_runtime.core.evidence")


class EvidenceUploader(Protocol):
    async def upload(
        self,
        frame: Any,
        *,
        device_id: str,
        camera_id: str,
        violation_type: str,
        recorded_at: dt.datetime,
    ) -> str | None: ...


class HttpEvidenceUploader:
    """Encode a frame as JPEG and upload it to the server evidence endpoint."""

    def __init__(
        self,
        base_url: str,
        *,
        token: str | None = None,
        timeout_s: float = 15.0,
        jpeg_quality: int = 85,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout_s
        self._quality = max(1, min(jpeg_quality, 100))

    async def upload(
        self,
        frame: Any,
        *,
        device_id: str,
        camera_id: str,
        violation_type: str,
        recorded_at: dt.datetime,
    ) -> str | None:
        from vision_runtime.capture.frame_source import NO_CV2_FRAME

        if frame is NO_CV2_FRAME:  # capture disabled / no cv2 — nothing to upload
            return None

        try:
            import cv2
        except ModuleNotFoundError:
            logger.warning("OpenCV is unavailable; skipping evidence upload")
            return None

        encoded_ok, encoded = cv2.imencode(
            ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, self._quality]
        )
        if not encoded_ok:
            logger.warning("could not encode evidence frame")
            return None

        filename = f"{camera_id}-{recorded_at.strftime('%Y%m%dT%H%M%S%fZ')}.jpg"
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        files = {"file": (filename, encoded.tobytes(), "image/jpeg")}
        data = {
            "device_id": device_id,
            "camera_id": camera_id,
            "violation_type": violation_type,
            "recorded_at": recorded_at.isoformat(),
        }

        async with HttpClient(
            self._base_url,
            headers=headers,
            timeout=self._timeout,
        ) as client:
            response = await client.post(
                "/evidence",
                data=data,
                files=files,
            )
            image_path = response.json().get("image_path")
            return str(image_path) if image_path else None


__all__ = ["EvidenceUploader", "HttpEvidenceUploader"]