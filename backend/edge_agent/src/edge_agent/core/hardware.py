"""Auto-detect edge hardware at startup, in the spirit of ``ultralytics.select_device()``.

One probe on boot decides two things:

* **backend** — the whole capture->infer->publish strategy (``composed`` runs
  anywhere; ``deepstream`` fuses the pipeline on NVIDIA GPUs / Jetson).
* **device** — the compute target handed to the inference runtime
  (``cuda:0`` / ``mps`` / ``cpu``).

Both accept an explicit override, exactly like ``select_device("cpu")``:

    VISION__BACKEND=auto   VISION__DEVICE=auto      # probe and pick
    VISION__BACKEND=composed  VISION__DEVICE=cpu    # force

The result also carries what artifact formats this box can load, so the
control plane can ship the right model variant (see ``model_formats``).
"""

from __future__ import annotations

import logging
import platform
import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger("edge_agent.hardware")

_H264_ENCODER_KEYS = {
    "h264_nvenc": "nvenc",
    "h264_vaapi": "vaapi",
    "h264_v4l2m2m": "v4l2m2m",
    "libx264": "libx264",
}


@dataclass(frozen=True)
class Hardware:
    """Immutable snapshot of what this device can do. Probe via :func:`detect_hardware`."""

    arch: str  # x86_64 | aarch64 | arm64 | ...
    is_jetson: bool
    has_cuda: bool
    has_mps: bool  # Apple Silicon Metal
    has_deepstream: bool  # `pyds` importable
    encoders: frozenset[str]  # subset of {nvenc, vaapi, v4l2m2m, libx264}

    backend: str  # resolved: composed | deepstream
    device: str  # resolved: cpu | cuda:0 | mps
    model_formats: tuple[str, ...]  # artifact formats this box can load, best first

    def as_dict(self) -> dict:
        return {
            "arch": self.arch,
            "is_jetson": self.is_jetson,
            "accelerators": sorted(self.accelerators),
            "backend": self.backend,
            "device": self.device,
            "encoders": sorted(self.encoders),
            "model_formats": list(self.model_formats),
        }

    @property
    def accelerators(self) -> set[str]:
        acc: set[str] = set()
        if self.has_cuda:
            acc.add("cuda")
        if self.has_mps:
            acc.add("mps")
        if self.has_deepstream:
            acc.add("deepstream")
        acc |= {e for e in self.encoders if e != "libx264"}
        return acc


@lru_cache(maxsize=1)
def _ffmpeg_encoders() -> frozenset[str]:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return frozenset()
    try:
        out = subprocess.run(  # noqa: S603
            [ffmpeg, "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout
    except Exception:  # noqa: BLE001
        return frozenset()
    names = {line.split()[1] for line in out.splitlines() if line.startswith(" V")}
    return frozenset(key for enc, key in _H264_ENCODER_KEYS.items() if enc in names)


@lru_cache(maxsize=1)
def _is_jetson() -> bool:
    try:
        with open("/proc/device-tree/model", encoding="utf-8", errors="replace") as fh:  # noqa: PTH123
            return "NVIDIA Jetson" in fh.read()
    except OSError:
        return False


@lru_cache(maxsize=1)
def _has_cuda() -> bool:
    nvidia_smi = shutil.which("nvidia-smi") is not None
    if not nvidia_smi and not _is_jetson():
        return False
    try:
        import torch  # noqa: PLC0415

        return bool(torch.cuda.is_available())
    except Exception:  # noqa: BLE001 - torch missing / broken: fall back to the CLI signal
        return nvidia_smi or _is_jetson()


@lru_cache(maxsize=1)
def _has_mps() -> bool:
    try:
        import torch  # noqa: PLC0415

        return bool(torch.backends.mps.is_available())
    except Exception:  # noqa: BLE001
        return False


@lru_cache(maxsize=1)
def _has_deepstream() -> bool:
    try:
        import pyds  # noqa: F401, PLC0415

        return True
    except Exception:  # noqa: BLE001
        return False


def _resolve_device(requested: str, *, has_cuda: bool, has_mps: bool) -> str:
    if requested and requested != "auto":
        if requested.startswith("cuda") and not has_cuda:
            logger.warning("device=%s requested but CUDA unavailable; using cpu", requested)
            return "cpu"
        if requested == "mps" and not has_mps:
            logger.warning("device=mps requested but MPS unavailable; using cpu")
            return "cpu"
        return requested
    if has_cuda:
        return "cuda:0"
    if has_mps:
        return "mps"
    return "cpu"


def _resolve_backend(requested: str, *, has_deepstream: bool, has_cuda: bool) -> str:
    if requested and requested != "auto":
        if requested == "deepstream" and not (has_deepstream and has_cuda):
            logger.warning(
                "backend=deepstream requested but pyds/CUDA missing; using composed"
            )
            return "composed"
        return requested
    return "deepstream" if (has_deepstream and has_cuda) else "composed"


def _model_formats(backend: str, *, has_cuda: bool, arch: str) -> tuple[str, ...]:
    fmts: list[str] = []
    if backend == "deepstream":
        fmts += ["engine", "onnx"]
    else:
        if has_cuda:
            fmts += ["engine", "pt"]
        if arch in ("arm64", "aarch64"):
            fmts += ["tflite"]
        fmts.append("onnx")
    # de-dupe, keep order
    return tuple(dict.fromkeys(fmts))


def detect_hardware(*, backend: str = "auto", device: str = "auto") -> Hardware:
    """Probe the host once and resolve ``backend`` / ``device``.

    ``backend`` / ``device`` of ``"auto"`` (the default) let the probe decide;
    any other value forces that choice, downgrading with a warning if the
    hardware can't honour it.
    """
    arch = platform.machine().lower()
    is_jetson = _is_jetson()
    has_cuda = _has_cuda()
    has_mps = _has_mps()
    has_ds = _has_deepstream()
    encoders = _ffmpeg_encoders()

    resolved_backend = _resolve_backend(backend, has_deepstream=has_ds, has_cuda=has_cuda)
    resolved_device = _resolve_device(device, has_cuda=has_cuda, has_mps=has_mps)
    formats = _model_formats(resolved_backend, has_cuda=has_cuda, arch=arch)

    hw = Hardware(
        arch=arch,
        is_jetson=is_jetson,
        has_cuda=has_cuda,
        has_mps=has_mps,
        has_deepstream=has_ds,
        encoders=encoders,
        backend=resolved_backend,
        device=resolved_device,
        model_formats=formats,
    )
    logger.info(
        "hardware: arch=%s jetson=%s cuda=%s mps=%s deepstream=%s encoders=%s "
        "-> backend=%s device=%s formats=%s",
        arch,
        is_jetson,
        has_cuda,
        has_mps,
        has_ds,
        sorted(encoders),
        hw.backend,
        hw.device,
        list(formats),
    )
    return hw


__all__ = ["Hardware", "detect_hardware"]
