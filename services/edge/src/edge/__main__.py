"""Starts the edge runtime: `python -m edge` (settings from EDGE_* environment variables or .env)."""

import logging
import signal
import threading

from edge.bootstrap.container import build_container
from edge.bootstrap.settings import Settings


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    container = build_container(Settings())
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    container.start()
    stop.wait()
    container.stop()


if __name__ == "__main__":
    main()
