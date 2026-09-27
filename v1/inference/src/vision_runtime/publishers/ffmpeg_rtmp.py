"""Publish a camera to a MediaMTX RTMP ingest endpoint via ``ffmpeg``.

WHIP would be tidier (one port, token in the same request) but ffmpeg's WHIP
muxer can't complete an ICE handshake with MediaMTX. RTMP is a plain-TCP push
that never fails on NAT/DTLS, takes credentials as ``?user=&pass=`` query
params (so a dotted JWT survives), and MediaMTX repackages it to WebRTC for
browser viewers with no transcode.

Enabled by ``VR_RTMP_BASE`` (e.g. ``rtmp://host:1935``); the publisher then
ignores the issued WHIP URL and pushes to ``{VR_RTMP_BASE}/{path}`` with the
stream token as ``pass``.
"""

from __future__ import annotations

import asyncio
import logging
import os
from urllib.parse import quote, urlsplit

from vision_runtime.publishers.base import VideoPublisher
from vision_runtime.publishers.ffmpeg_whip import _input_args, resolve_encoder

logger = logging.getLogger("vision_runtime.publishers")


def _rtmp_target(whip_url: str, token: str) -> str:
    base = os.environ["VR_RTMP_BASE"].rstrip("/")
    path = urlsplit(whip_url).path.strip("/").removesuffix("/whip").strip("/") or "stream"
    return f"{base}/{path}?user=edge&pass={quote(token, safe='')}"


class FfmpegRtmpPublisher(VideoPublisher):
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
        target = _rtmp_target(whip_url, token)
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "warning",
            *_input_args(source, loop=loop),
            "-r",
            os.environ.get("VR_STREAM_FPS", "15"),
            "-c:v",
            encoder,
            *encoder_args,
            "-b:v",
            f"{self._bitrate_kbps}k",
            "-pix_fmt",
            "yuv420p",
            # WebRTC decoders expect constrained-baseline H264; libx264 defaults
            # to High profile, which many browsers render as a black frame.
            "-profile:v",
            "baseline",
            "-level",
            "3.1",
            "-bf",
            "0",
            "-g",
            os.environ.get("VR_RTMP_GOP", "10"),
            "-muxdelay",
            "0",
            "-muxpreload",
            "0",
            "-flush_packets",
            "1",
            "-flvflags",
            "no_duration_filesize",
            "-an",
            "-f",
            "flv",
            target,
        ]
        logger.info(
            "starting ffmpeg rtmp publisher: encoder=%s target=%s",
            encoder,
            target.split("?")[0],
        )
        self._process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
        )
        asyncio.create_task(self._log_stderr(), name="ffmpeg-rtmp-stderr")

    async def _log_stderr(self) -> None:
        if self._process is None or self._process.stderr is None:
            return
        async for line in self._process.stderr:
            logger.debug("ffmpeg: %s", line.decode(errors="replace").rstrip())
        # stderr closed => process exited; reap it so `.returncode` is set.
        if self._process is not None:
            await self._process.wait()

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


__all__ = ["FfmpegRtmpPublisher"]
