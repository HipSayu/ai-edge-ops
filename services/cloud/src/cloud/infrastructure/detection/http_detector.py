import base64

import httpx

from cloud.domain.violation.detection import DetectionResult, FoundObject
from shared.errors import ServiceUnavailable


class HttpPpeDetector:
    """The PpeDetector port: the detector app, which runs the PPE model (POST /detect with the picture's bytes)."""

    def __init__(self, base_url: str, timeout_sec: float = 60.0) -> None:
        self._url = base_url.rstrip("/") + "/detect"
        self._timeout = timeout_sec

    def detect(self, image: bytes) -> DetectionResult:
        try:
            response = httpx.post(self._url, content=image, headers={"Content-Type": "application/octet-stream"}, timeout=self._timeout)
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as e:
            raise ServiceUnavailable(f"Không gọi được bộ nhận diện PPE: {e}") from e
        return DetectionResult(
            objects=tuple(
                FoundObject(d["label"], float(d["confidence"]), tuple(int(v) for v in d["box"])) for d in body["detections"]
            ),
            annotated_jpeg=base64.b64decode(body["annotated_jpeg_b64"]),
        )
