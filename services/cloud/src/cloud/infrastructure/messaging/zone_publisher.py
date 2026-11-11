"""The ZonePublisher port over MQTT: the zones of a camera, retained, on the topic the camera's node listens to."""

from collections.abc import Callable
from typing import Any

from edge_link import ZoneSpec, ZonesMessage, ZonesPublisher
from edge_link.publisher import default_client

from cloud.domain.model.zone import Zone


class MqttZonePublisher:
    def __init__(
        self, host: str, port: int = 1883, username: str | None = None, password: str | None = None,
        tls_ca: str | None = None, client_factory: Callable[[str], Any] = default_client,
    ) -> None:
        self._link = ZonesPublisher(host, port, username, password, client_factory, client_id="cloud-zones", tls_ca=tls_ca)

    def start(self) -> None:
        self._link.start()

    def stop(self) -> None:
        self._link.stop()

    def publish(self, camera_id: int, zones: list[Zone]) -> bool:
        specs = tuple(ZoneSpec(z.id, z.name, z.polygon, z.enabled) for z in zones if z.id is not None)
        return self._link.publish(ZonesMessage(camera_id, specs))
