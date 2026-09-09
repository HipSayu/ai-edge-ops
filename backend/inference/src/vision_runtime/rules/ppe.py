"""Pure PPE detection rule helpers."""

from __future__ import annotations

from vision_runtime.runtime import Detection


def evaluate_ppe(detections: list[Detection], required: list[str]) -> list[str]:
    """Return violation labels for missing or explicitly negative PPE classes."""
    if not any(detection.label == "person" for detection in detections):
        return []
    present = {detection.label for detection in detections}
    violations = [f"no_{item}" for item in required if item not in present]
    violations += [detection.label for detection in detections if detection.label.startswith("no_")]
    return sorted(set(violations))


__all__ = ["evaluate_ppe"]