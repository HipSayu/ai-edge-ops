from hopquangdo.messaging import PubSub

from src.shared.config import MqttSettings


class MqttPubSubFactory:
    """Builds the MQTT PubSub from any settings that include the MqttSettings block."""

    @staticmethod
    def create(
        settings: MqttSettings,
        client_id: str,
        will_topic: str | None = None,
        will_payload: str | None = None,
    ) -> PubSub:
        from hopquangdo.messaging.adapters.mqtt import MqttConfig, MqttPubSub

        return MqttPubSub(
            MqttConfig(
                host=settings.mqtt_host,
                port=settings.mqtt_port,
                client_id=client_id,
                username=settings.mqtt_username,
                password=settings.mqtt_password,
                tls=settings.mqtt_tls,
                will_topic=will_topic,
                will_payload=will_payload,
            )
        )
