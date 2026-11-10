"""Wires the edge runtime's adapters into its use cases, once."""

from dataclasses import dataclass

from edge_link import ZonesSubscriber

from edge.application.durable_publisher import DurablePublisher
from edge.application.pipeline import CameraPipeline
from edge.application.runtime import EdgeRuntime
from edge.application.zone_book import ZoneBook
from edge.bootstrap.settings import Settings
from edge.domain.confirmation import Confirmation
from edge.domain.cooldown import Cooldown
from edge.infrastructure.alarm import CommandAlarm, HttpAlarm, LogAlarm, MultiAlarm
from edge.infrastructure.batching_detector import BatchingDetector
from edge.infrastructure.bytetrack_tracker import ByteTrackTracker
from edge.infrastructure.jpeg_renderer import JpegRenderer
from edge.infrastructure.mqtt_publisher import MqttEventPublisher
from edge.infrastructure.sqlite_outbox import SqliteOutbox
from edge.infrastructure.video_source import VideoFileSource
from edge.infrastructure.yolo_detector import YoloDetector
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
    detector = YoloDetector(settings.model_path, settings.infer_imgsz, settings.conf, settings.torch_threads, settings.device)  # one model for every camera
    if settings.batch_max > 1 and settings.device != "cpu":  # on a CPU a batch is no faster than its frames one by one
        detector = BatchingDetector(detector, settings.batch_max, settings.batch_gather_ms / 1000)
    renderer = JpegRenderer()
    alarm = build_alarm(settings)
    nodes = settings.node_configs()
    links: list[NodeLink] = []
    pipelines: list[CameraPipeline] = []
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
        pipelines += [
            CameraPipeline(
                node_id=node.node_id, camera_id=camera.id,
                source=VideoFileSource(camera.video, max_fps=settings.video_max_fps), detector=detector,
                renderer=renderer, publisher=sender, violation_classes=frozenset(settings.violation_classes),
                every_n=settings.infer_every_n_frames, cooldown=Cooldown(settings.event_cooldown_sec),
                tracker=ByteTrackTracker(settings.track_buffer) if settings.tracking else None,  # one per camera
                confirmation=Confirmation(settings.min_frames, settings.forget_after_sec),
                detection_sink=mqtt if settings.publish_detections else None,  # straight to the link: a box is not worth queueing
                zones=book if settings.zones_enabled else None, alarm=alarm,
                zone_classes=frozenset(settings.zone_classes), zone_cooldown=Cooldown(settings.zone_cooldown_sec),
                zone_confirmation=Confirmation(settings.min_frames, settings.forget_after_sec),
            )
            for camera in node.cameras
        ]
    return Container(EdgeRuntime(pipelines), links)


def build_alarm(settings: Settings) -> MultiAlarm:
    """What sounds when someone enters a zone: always a log line, plus a command and/or a URL when they are configured."""
    sinks = [LogAlarm()]
    if settings.alarm_command:
        sinks.append(CommandAlarm(settings.alarm_command))
    if settings.alarm_url:
        sinks.append(HttpAlarm(settings.alarm_url))
    return MultiAlarm(sinks)
