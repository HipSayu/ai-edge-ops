"""Video publisher — pluggable, one instance per streaming camera.

``build_publisher("ffmpeg")`` works unmodified on Jetson, Raspberry Pi, or a
plain x86 box: the hardware encoder is resolved at runtime by
:func:`vision_runtime.publishers.ffmpeg_whip.resolve_encoder`, not hardcoded per
device. Video never touches inference/pipeline.py's frames — this reads the
camera source directly and dials out to WHIP on its own.
"""

from __future__ import annotations

import os

from vision_runtime.publishers.base import VideoPublisher
from vision_runtime.publishers.null import NullPublisher


def build_publisher(
    kind: str = "ffmpeg", *, encoder: str = "auto", bitrate_kbps: int = 2000
) -> VideoPublisher:
    if kind == "ffmpeg":
        # VR_RTMP_BASE routes the publish over RTMP instead of WHIP — ffmpeg's
        # WHIP muxer can't complete an ICE handshake with MediaMTX.
        if os.environ.get("VR_RTMP_BASE"):
            from vision_runtime.publishers.ffmpeg_rtmp import FfmpegRtmpPublisher

            return FfmpegRtmpPublisher(encoder=encoder, bitrate_kbps=bitrate_kbps)
        from vision_runtime.publishers.ffmpeg_whip import FfmpegWhipPublisher

        return FfmpegWhipPublisher(encoder=encoder, bitrate_kbps=bitrate_kbps)
    return NullPublisher()


__all__ = ["NullPublisher", "VideoPublisher", "build_publisher"]
