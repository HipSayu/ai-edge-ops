"""Running the PPE model on a one-off picture from the dashboard, to test it without a camera."""

from cloud.application.ports import PpeDetector
from cloud.domain.violation.detection import DetectionResult
from shared.errors import Invalid, ServiceUnavailable

MAX_IMAGE_BYTES = 8 * 1024 * 1024


class DetectService:
    def __init__(self, detector: PpeDetector | None) -> None:
        self._detector = detector

    def detect(self, image: bytes) -> DetectionResult:
        if self._detector is None:
            raise ServiceUnavailable("Chưa cấu hình bộ nhận diện PPE (CLOUD_DETECTOR_URL)")
        if not image:
            raise Invalid("Ảnh trống")
        if len(image) > MAX_IMAGE_BYTES:
            raise Invalid(f"Ảnh quá lớn (tối đa {MAX_IMAGE_BYTES // 1024 // 1024} MB)")
        return self._detector.detect(image)
