"""Encoding of the frames the feeds publish."""

import cv2
import numpy as np

_MAX_SIDE = 960  # the web shows a tile, not the full frame; the boxes are in the original pixels and are scaled by the page


def encode_jpeg(frame: np.ndarray) -> bytes:
    height, width = frame.shape[:2]
    if max(height, width) > _MAX_SIDE:
        scale = _MAX_SIDE / max(height, width)
        frame = cv2.resize(frame, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return buf.tobytes() if ok else b""


def placeholder_jpeg(text: str) -> bytes:
    img = np.full((360, 640, 3), 24, dtype=np.uint8)
    cv2.putText(img, text, (170, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (160, 160, 160), 2)
    return encode_jpeg(img)
