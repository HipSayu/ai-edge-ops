"""Pluggable video publisher — mirrors ``runtime/base.py``'s shape.

A publisher owns one outbound WHIP connection for one camera: capture the
camera's own source (not the inference loop's frames — this is a raw,
separate ffmpeg process reading straight from the device) and push H264 to
the URL/token the control plane issued. Bbox metadata never goes through
here; see ``edge_agent.link.EdgeLink.send_bbox_frame`` for that.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class VideoPublisher(ABC):
    @abstractmethod
    async def start(self, *, source: str, whip_url: str, token: str, loop: bool = False) -> None:
        """Begin publishing ``source`` to ``whip_url`` (WHIP, bearer ``token``)."""

    @abstractmethod
    async def stop(self) -> None: ...

    @property
    @abstractmethod
    def running(self) -> bool: ...
