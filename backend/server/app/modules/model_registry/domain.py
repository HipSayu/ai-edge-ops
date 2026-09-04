"""Model registry domain: enums and rules."""

from __future__ import annotations

from app.shared.enum import StrEnum


class ModelTask(StrEnum):
    DETECTION = "detection"
    SEGMENTATION = "segmentation"
    POSE = "pose"
    CLASSIFICATION = "classification"


class ModelFormat(StrEnum):
    PYTORCH = "pt"
    ONNX = "onnx"
    TENSORRT = "engine"
    OPENVINO = "openvino"


class CompressionMethod(StrEnum):
    NONE = "none"
    PRUNING = "pruning"
    QAT = "qat"
    DISTILLATION = "distillation"


class ModelVersionStatus(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    PUBLISHED = "published"  # deployable
    ARCHIVED = "archived"


DEPLOYABLE_STATUSES = frozenset({ModelVersionStatus.PUBLISHED})
