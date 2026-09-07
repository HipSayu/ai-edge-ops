"""Video publisher — pluggable, one instance per streaming camera.

``build_publisher("ffmpeg")`` works unmodified on Jetson, Raspberry Pi, or a
plain x86 box: the hardware encoder is resolved at runtime by
:func:`edge_agent.streaming.ffmpeg_whip.resolve_encoder`, not hardcoded per
device. Video never touches inference/pipeline.py's frames — this reads the
camera source directly and dials out to WHIP on its own.
"""

from __future__ import annotations

from edge_agent.streaming.base import VideoPublisher
from edge_agent.streaming.null import NullPublisher


def build_publisher(
    kind: str = "ffmpeg", *, encoder: str = "auto", bitrate_kbps: int = 2000
) -> VideoPublisher:
    if kind == "ffmpeg":
        from edge_agent.streaming.ffmpeg_whip import FfmpegWhipPublisher

        return FfmpegWhipPublisher(encoder=encoder, bitrate_kbps=bitrate_kbps)
    return NullPublisher()


__all__ = ["NullPublisher", "VideoPublisher", "build_publisher"]
