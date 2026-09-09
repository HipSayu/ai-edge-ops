"""Publish a camera to a WHIP endpoint via the ``ffmpeg`` binary.

No GStreamer/PyGObject dependency: ffmpeg ships a WHIP muxer since 6.1
(``-f whip``), and static builds exist for every architecture we care about
(x86_64, aarch64/Jetson, armhf/RPi). Which encoder to use is the only thing
that changes per device — see :func:`resolve_encoder`.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import shutil

from vision_runtime.publish.base import VideoPublisher

logger = logging.getLogger("vision_runtime.publish")

# preferred -> [(encoder name, extra args)], tried in order, first available wins.
_HARDWARE_ENCODERS: dict[str, tuple[str, list[str]]] = {
    "v4l2m2m": ("h264_v4l2m2m", []),  # Jetson (JetPack ffmpeg build) / Raspberry Pi
    "vaapi": ("h264_vaapi", ["-vaapi_device", "/dev/dri/renderD128"]),  # Intel/AMD iGPU
    "nvenc": ("h264_nvenc", []),  # discrete NVIDIA GPU (desktop/server, not Jetson)
}
_SOFTWARE_ENCODER = ("libx264", ["-preset", "veryfast", "-tune", "zerolatency"])


@functools.lru_cache(maxsize=1)
def _available_encoders() -> frozenset[str]:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return frozenset()
    try:
        import subprocess  # noqa: PLC0415

        out = subprocess.run(
            [ffmpeg, "-hide_banner", "-encoders"], capture_output=True, text=True, timeout=10
        ).stdout
    except Exception:  # noqa: BLE001
        return frozenset()
    return frozenset(line.split()[1] for line in out.splitlines() if line.startswith(" V"))


def resolve_encoder(preferred: str) -> tuple[str, list[str]]:
    """``preferred``: "auto", one of ``_HARDWARE_ENCODERS`` keys, or a raw ffmpeg encoder name.

    "auto" probes ``ffmpeg -encoders`` and picks the first hardware encoder
    available on this box, falling back to software libx264 — this is what
    makes one agent build run unmodified on a Jetson, a Raspberry Pi, and a
    plain x86 dev box.
    """
    available = _available_encoders()
    if preferred == "auto":
        for name, args in _HARDWARE_ENCODERS.values():
            if name in available:
                return name, args
        return _SOFTWARE_ENCODER
    if preferred in _HARDWARE_ENCODERS:
        name, args = _HARDWARE_ENCODERS[preferred]
        if name in available:
            return name, args
        logger.warning("encoder %r unavailable on this device, falling back to libx264", preferred)
        return _SOFTWARE_ENCODER
    return preferred, []


def _input_args(source: str, *, loop: bool) -> list[str]:
    if source.isdigit():
        return ["-f", "v4l2", "-i", f"/dev/video{source}"]
    if source.startswith(("rtsp://", "http://", "https://")):
        return ["-i", source]
    args = ["-stream_loop", "-1"] if loop else []
    return [*args, "-i", source]


class FfmpegWhipPublisher(VideoPublisher):
    def __init__(self, *, encoder: str = "auto", bitrate_kbps: int = 2000) -> None:
        self._encoder_pref = encoder
        self._bitrate_kbps = bitrate_kbps
        self._process: asyncio.subprocess.Process | None = None

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.returncode is None

    async def start(self, *, source: str, whip_url: str, token: str, loop: bool = False) -> None:
        await self.stop()
        encoder, encoder_args = resolve_encoder(self._encoder_pref)
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "warning",
            *_input_args(source, loop=loop),
            "-c:v",
            encoder,
            *encoder_args,
            "-b:v",
            f"{self._bitrate_kbps}k",
            "-pix_fmt",
            "yuv420p",
            "-an",
            "-f",
            "whip",
            "-headers",
            f"Authorization: Bearer {token}\r\n",
            whip_url,
        ]
        logger.info("starting ffmpeg whip publisher: encoder=%s url=%s", encoder, whip_url)
        self._process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
        )
        asyncio.create_task(self._log_stderr(), name="ffmpeg-whip-stderr")

    async def _log_stderr(self) -> None:
        if self._process is None or self._process.stderr is None:
            return
        async for line in self._process.stderr:
            logger.debug("ffmpeg: %s", line.decode(errors="replace").rstrip())

    async def stop(self) -> None:
        if self._process is None:
            return
        if self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
        self._process = None


__all__ = ["FfmpegWhipPublisher", "resolve_encoder"]
