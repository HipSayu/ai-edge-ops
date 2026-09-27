"""Vision runtime — camera capture + model inference + WHIP publish.

Built into a per-model OCI image (one variant per edge backend). Runs as the
``inference`` compose service next to the edge agent, talking to it over a local
unix socket (:mod:`edge_protocol.channel`). Public surface: :class:`VisionWorker`.
"""

from __future__ import annotations

from vision_runtime.core.worker import VisionWorker

__all__ = ["VisionWorker"]
