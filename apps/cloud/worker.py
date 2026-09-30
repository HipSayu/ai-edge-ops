"""Cloud worker: consumes edge state/telemetry/events from MQTT and sweeps node liveness.

Only needed when the worker scales apart from the API (CLOUD_EMBEDDED_WORKER=false).
Run: python -m apps.cloud.worker (from repo root).
"""

import asyncio
import sys

from hopquangdo.observability import LoggingSetup

from src.cloud.bootstrap.cloud_container import CloudContainer
from src.cloud.config.cloud_settings import CloudSettings


async def main() -> None:
    settings = CloudSettings(service_name="cloud-worker")
    LoggingSetup.configure(settings.service_name, settings.log_level, settings.log_json)
    container = CloudContainer(settings)
    await container.start()
    try:
        await container.subscribe_consumers()
        await container.node_liveness_service.run()
    finally:
        await container.stop()


if __name__ == "__main__":
    # paho-mqtt needs add_reader, which the default Windows Proactor loop lacks
    asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop if sys.platform == "win32" else None)
