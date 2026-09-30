import uuid

from hopquangdo.messaging import PubSub

from src.cloud.application.services.realtime_service import RealtimeService
from src.cloud.config.cloud_settings import CloudSettings
from src.shared.contracts import EdgeTopics
from src.shared.infrastructure.messaging.mqtt_pubsub_factory import MqttPubSubFactory


class RealtimeContainer:
    """Composition root for the WS service: MQTT in, WebSocket out. No database."""

    def __init__(self, settings: CloudSettings, pubsub: PubSub | None = None) -> None:
        self.settings = settings
        self.pubsub = pubsub or MqttPubSubFactory.create(settings, f"{settings.service_name}-ws-{uuid.uuid4().hex[:8]}")
        self.realtime_service = RealtimeService()

    async def start(self) -> None:
        await self.pubsub.connect()
        for topic in (EdgeTopics.all_states(), EdgeTopics.all_telemetry(), EdgeTopics.all_events(), EdgeTopics.all_logs()):
            await self.pubsub.subscribe(topic, self.realtime_service.publish)

    async def stop(self) -> None:
        await self.pubsub.disconnect()

    async def check_broker(self) -> bool:
        return self.pubsub.is_connected
