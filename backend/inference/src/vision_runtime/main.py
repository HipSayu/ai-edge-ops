"""Entrypoint: serve the agent IPC socket, run the vision worker forever.

    python -m vision_runtime       (or: vision-runtime)
"""

from __future__ import annotations

import asyncio
import logging

from edge_protocol.channel import TcpChannel, UnixSocketChannel

from vision_runtime.config import WorkerSettings, load_settings
from vision_runtime.core.worker import VisionWorker

logger = logging.getLogger("vision_runtime")


async def run(settings: WorkerSettings | None = None) -> None:
    settings = settings or load_settings()
    logging.basicConfig(level=settings.log_level)
    logger.info("vision-runtime up: runtime=%s socket=%s", settings.runtime, settings.socket_path)

    while True:
        channel_type = TcpChannel if settings.socket_path.startswith("tcp://") else UnixSocketChannel
        channel = await channel_type.serve_one(settings.socket_path)
        logger.info("agent connected")
        worker = VisionWorker(settings, channel)
        try:
            await worker.run()
        except Exception:  # noqa: BLE001 - one dropped agent link must not kill the process
            logger.exception("worker loop ended")
        logger.info("agent disconnected; waiting for reconnect")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
