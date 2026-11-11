"""Wires adapters into use cases, once. The only place that knows both sides."""

from dataclasses import dataclass

from edge_link import EventSubscriber, SeenEvents
from redis import Redis
from sqlalchemy import Engine

from cloud.application.usecases.analytics_service import AnalyticsService
from cloud.application.usecases.auth_service import AuthService
from cloud.application.usecases.camera_service import CameraService
from cloud.application.usecases.chat_files_service import ChatImageService, KnowledgeService, ReportService
from cloud.application.usecases.chat_service import ChatService
from cloud.application.usecases.catalog_service import CatalogService
from cloud.application.usecases.cluster_service import ClusterService
from cloud.application.usecases.detect_service import DetectService
from cloud.application.usecases.monitoring_service import MonitoringService
from cloud.application.usecases.node_service import NodeService
from cloud.application.usecases.user_service import UserService
from cloud.application.usecases.violation_recorder import ViolationRecorder
from cloud.application.usecases.violation_service import ViolationService
from cloud.application.usecases.zone_service import ZoneService
from cloud.bootstrap.settings import Settings
from cloud.bootstrap.edge_events import build_edge_events
from cloud.infrastructure.messaging.redis_seen import RedisSeenEvents
from cloud.infrastructure.messaging.dunly_chat import DunlyChat
from cloud.infrastructure.files.image_store import FileImageStore
from cloud.infrastructure.knowledge.knowledge_base import DocumentKnowledgeBase
from cloud.infrastructure.knowledge.qdrant_store import QdrantVectorStore
from cloud.infrastructure.llm.http_embedder import HttpEmbedder
from cloud.infrastructure.files.report_store import FileReportStore
from cloud.infrastructure.messaging.zone_publisher import MqttZonePublisher
from cloud.infrastructure.persistence.database import create_engine_for, create_schema, make_session_factory
from cloud.infrastructure.persistence.seed import seed_if_empty
from cloud.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from cloud.infrastructure.security.passwords import Pbkdf2PasswordHasher
from cloud.infrastructure.security.tokens import RsaTokenIssuer
from cloud.infrastructure.files.snapshot_store import FileSnapshotStore
from cloud.infrastructure.files.video_store import FileVideoStore
from cloud.infrastructure.detection.detections import DetectionStore
from cloud.infrastructure.detection.hub import FeedHub
from cloud.infrastructure.detection.http_detector import HttpPpeDetector
from qdrant_client import QdrantClient


@dataclass
class Container:
    settings: Settings
    auth: AuthService
    users: UserService
    clusters: ClusterService
    nodes: NodeService
    cameras: CameraService
    catalog: CatalogService
    monitoring: MonitoringService
    violations: ViolationService
    analytics: AnalyticsService
    detect: DetectService
    zones: ZoneService
    chat: ChatService
    chat_images: ChatImageService
    reports: ReportService
    knowledge: KnowledgeService
    tokens: RsaTokenIssuer
    _feeds: FeedHub
    _engine: Engine
    _edge_events: EventSubscriber | None = None
    _zone_link: MqttZonePublisher | None = None

    def start(self) -> None:
        """Starts a feed for every enabled camera, and listens to the edge runtimes when a broker is set."""
        self.cameras.resume_feeds()
        if self._edge_events is not None:
            self._edge_events.start()
        if self._zone_link is not None:
            self._zone_link.start()
            self.zones.publish_all()

    def shutdown(self) -> None:
        if self._edge_events is not None:
            self._edge_events.stop()
        if self._zone_link is not None:
            self._zone_link.stop()
        self._feeds.stop_all()
        self._engine.dispose()


def build_container(settings: Settings) -> Container:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.video_dir.mkdir(parents=True, exist_ok=True)

    engine = create_engine_for(settings.resolved_database_url())
    create_schema(engine)
    session_factory = make_session_factory(engine)
    seed_if_empty(session_factory)

    def uow() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    videos = FileVideoStore(settings.video_dir)
    snapshots = FileSnapshotStore(settings.snapshot_dir)
    recorder = ViolationRecorder(uow, snapshots)
    feeds = FeedHub()
    detections = DetectionStore()
    seen: SeenEvents | None = (
        RedisSeenEvents(Redis.from_url(settings.redis_url), settings.event_seen_ttl_sec) if settings.redis_url else None
    )

    def on_detections(message) -> None:
        detections.add(message)
        feeds.follow(message.camera_id, message.video_ts_sec)

    edge_events = build_edge_events(settings, recorder.record, seen, on_detections=on_detections)

    zone_link = MqttZonePublisher(
        settings.mqtt_host, settings.mqtt_port, settings.mqtt_username, settings.mqtt_password,
        str(settings.mqtt_tls_ca) if settings.mqtt_tls_ca else None,
    ) if settings.mqtt_host else None  # the zones reach the edge over the same broker the events come from
    clusters = ClusterService(uow, feeds)
    nodes = NodeService(uow, feeds)
    cameras = CameraService(uow, feeds, videos)
    tokens = RsaTokenIssuer(settings.jwt_private_key_path, settings.jwt_ttl_min)
    hasher = Pbkdf2PasswordHasher()
    detector = HttpPpeDetector(settings.detector_url) if settings.detector_url else None
    detect = DetectService(detector)
    chat_images = ChatImageService(FileImageStore(settings.image_dir), detect)
    regulations = None
    if settings.qdrant_url and settings.embedding_base_url:  # nothing connects until the first search
        regulations = DocumentKnowledgeBase(
            QdrantVectorStore(QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key), settings.qdrant_collection),
            HttpEmbedder(settings.embedding_base_url, settings.embedding_model, settings.embedding_api_key),
            settings.regulation_dir, settings.knowledge_min_score,
        )
    assistant = (
        DunlyChat(settings.dunly_url, settings.dunly_api_key, settings.dunly_agent)
        if settings.dunly_url and settings.dunly_api_key else None
    )
    return Container(
        settings=settings,
        auth=AuthService(uow, hasher, tokens),
        users=UserService(uow, hasher),
        clusters=clusters,
        nodes=nodes,
        cameras=cameras,
        catalog=CatalogService(uow, feeds, videos),
        monitoring=MonitoringService(uow, feeds, videos, snapshots, settings.grid_size, detections),
        violations=ViolationService(uow),
        analytics=AnalyticsService(uow),
        detect=detect,
        zones=ZoneService(uow, zone_link),
        chat=ChatService(assistant, chat_images),
        chat_images=chat_images,
        reports=ReportService(FileReportStore(settings.report_dir)),
        knowledge=KnowledgeService(regulations),
        tokens=tokens,
        _feeds=feeds,
        _engine=engine,
        _edge_events=edge_events,
        _zone_link=zone_link,
    )
