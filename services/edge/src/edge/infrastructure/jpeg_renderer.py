import cv2
import numpy as np

from edge.domain.detection import Detection

_COLOR = (40, 40, 230)  # BGR


class JpegRenderer:
    """The SnapshotRenderer port: boxes and labels drawn on a copy of the frame, encoded as a small JPEG."""

    def __init__(self, quality: int = 70, max_width: int = 960) -> None:
        self._quality, self._max_width = quality, max_width

    def render(self, image: np.ndarray, detections: list[Detection]) -> bytes:
        canvas = image.copy()
        for d in detections:
            x1, y1, x2, y2 = d.box
            cv2.rectangle(canvas, (x1, y1), (x2, y2), _COLOR, 2)
            cv2.putText(canvas, f"{d.label} {d.confidence:.2f}", (x1, max(y1 - 6, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, _COLOR, 1)
        height, width = canvas.shape[:2]
        if width > self._max_width:  # the message travels over the site's uplink: keep it small
            canvas = cv2.resize(canvas, (self._max_width, int(height * self._max_width / width)))
        ok, buffer = cv2.imencode(".jpg", canvas, [cv2.IMWRITE_JPEG_QUALITY, self._quality])
        if not ok:
            raise RuntimeError("could not encode the snapshot")
        return buffer.tobytes()
