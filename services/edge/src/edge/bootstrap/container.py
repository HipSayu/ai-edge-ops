"""Wires the edge runtime's adapters into its use cases, once."""

from dataclasses import dataclass

from edge_link import ZonesSubscriber

from edge.application.durable_publisher import DurablePublisher
from edge.application.camera_logic import CameraLogic
from edge.application.runtime import EdgeRuntime, NodeStream
from edge.application.zone_book import ZoneBook
from edge.bootstrap.config import CameraSource, Settings, deepstream_config
from edge.domain.confirmation import Confirmation
from edge.domain.cooldown import Cooldown
from edge.infrastructure.deepstream.pipeline import DeepStreamStream
from edge.infrastructure.alarm import CommandAlarm, HttpAlarm, LogAlarm, MultiAlarm
from edge.infrastructure.jpeg_renderer import JpegRenderer
from edge.infrastructure.mqtt_publisher import MqttEventPublisher
from edge.infrastructure.sqlite_outbox import SqliteOutbox
from edge.infrastructure.zone_sync import ZoneSync


@dataclass
class NodeLink:
    """What one node needs to reach the cloud."""

    mqtt: MqttEventPublisher
    sender: DurablePublisher  # what the cameras publish to: it writes to the outbox, the broker is reached from its own thread
    outbox: SqliteOutbox
    zones: ZonesSubscriber | None = None  # the zones the cloud draws for this node's cameras


@dataclass
class Container:
    runtime: EdgeRuntime
    links: list[NodeLink]

    def start(self) -> None:
        for link in self.links:
            link.mqtt.start()
            link.sender.start()
            if link.zones is not None:
                link.zones.start()
        self.runtime.start()

    def stop(self) -> None:
        self.runtime.stop()
        for link in self.links:
            if link.zones is not None:
                link.zones.stop()
            link.sender.stop()  # sends what it can, so it goes before the connection closes; the rest stays in the outbox
            link.mqtt.stop()
            link.outbox.close()


def build_container(settings: Settings) -> Container:
    renderer = JpegRenderer()
    alarm = build_alarm(settings)
    nodes = settings.node_configs()
    links: list[NodeLink] = []
    streams: list[NodeStream] = []
    for node in nodes:
        single = len(nodes) == 1
        mqtt = MqttEventPublisher(
            node.node_id, settings.mqtt_host, settings.mqtt_port,
            (settings.mqtt_username if single else None) or node.node_id, node.mqtt_password, tls_ca=settings.mqtt_tls_ca,
        )
        outbox_path = settings.outbox_path if single else settings.outbox_path.with_name(f"outbox-{node.node_id}.db")
        outbox = SqliteOutbox(outbox_path, settings.outbox_max_events)
        sender = DurablePublisher(outbox, mqtt)
        book = ZoneBook()
        zones_link = None
        if settings.zones_enabled:
            zones_path = settings.zones_path if single else settings.zones_path.with_name(f"zones-{node.node_id}.json")
            sync = ZoneSync(book, zones_path)
            sync.restore()
            zones_link = ZonesSubscriber(
                [camera.id for camera in node.cameras], settings.mqtt_host, settings.mqtt_port, sync.apply,
                (settings.mqtt_username if single else None) or node.node_id, node.mqtt_password,
                client_id=f"edge-zones-{node.node_id}", tls_ca=settings.mqtt_tls_ca,
            )
        links.append(NodeLink(mqtt, sender, outbox, zones_link))
        cameras = {
            camera.id: CameraLogic(
                node_id=node.node_id, camera_id=camera.id, renderer=renderer, publisher=sender,
                violation_classes=frozenset(settings.violation_classes), cooldown=Cooldown(settings.event_cooldown_sec),
                confirmation=Confirmation(settings.min_frames, settings.forget_after_sec),
                detection_sink=mqtt if settings.publish_detections else None,  # straight to the link: a box is not worth queueing
                zones=book if settings.zones_enabled else None, alarm=alarm,
                zone_classes=frozenset(settings.zone_classes), zone_cooldown=Cooldown(settings.zone_cooldown_sec),
                zone_confirmation=Confirmation(settings.min_frames, settings.forget_after_sec),
            )
            for camera in node.cameras
        }
        stream = DeepStreamStream(deepstream_config(settings, node.node_id, [CameraSource(c.id, c.uri) for c in node.cameras], len(nodes) > 1))
        streams.append(NodeStream(node.node_id, stream, cameras))
    return Container(EdgeRuntime(streams), links)


def build_alarm(settings: Settings) -> MultiAlarm:
    """What sounds when someone enters a zone: always a log line, plus a command and/or a URL when they are configured."""
    sinks = [LogAlarm()]
    if settings.alarm_command:
        sinks.append(CommandAlarm(settings.alarm_command))
    if settings.alarm_url:
        sinks.append(HttpAlarm(settings.alarm_url))
    return MultiAlarm(sinks)
