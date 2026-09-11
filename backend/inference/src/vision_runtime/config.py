"""Vision-runtime worker settings — env with ``__`` delimiter.

    SOCKET_PATH=/run/edge/inference.sock
    MODEL_DIR=/models
    MODEL_VERSION_ID=42
    RUNTIME=auto            # auto | yolo | onnx | dummy | deepstream
    DEVICE=auto             # auto | cpu | cuda:0 | mps
"""

from __future__ import annotations

from dqh.svc_core.config import BaseAppSettings
from pydantic import BaseModel, Field


class InferenceConfig(BaseModel):
    weights_dir: str = "/models"
    conf_threshold: float = 0.25
    iou_threshold: float = 0.5
    imgsz: int = 640
    classes: list[str] = Field(default_factory=lambda: ["helmet", "vest", "person"])
    ppe_required: list[str] = Field(default_factory=lambda: ["helmet", "vest"])


class WorkerSettings(BaseAppSettings):
    service_name: str = "vision-runtime"

    socket_path: str = "/run/edge/inference.sock"
    model_version_id: int | None = None      # the version this image was built for
    runtime: str = "auto"                    # auto | yolo | onnx | dummy | deepstream
    device: str = "auto"
    health_interval_s: float = 10.0
    min_violation_gap_s: float = 10.0

    inference: InferenceConfig = Field(default_factory=InferenceConfig)


def load_settings() -> WorkerSettings:
    """Build settings, first sourcing ``VR_ENV_FILE`` (e.g. deploy/.env.edge) into
    the process env so the ffmpeg publisher's ``VR_*`` knobs pick it up too when
    running as a bare process rather than a compose service."""
    import os
    from pathlib import Path

    env_file = os.environ.get("VR_ENV_FILE")
    if env_file and Path(env_file).is_file():
        from dotenv import load_dotenv

        load_dotenv(env_file, override=False)
    return WorkerSettings()
