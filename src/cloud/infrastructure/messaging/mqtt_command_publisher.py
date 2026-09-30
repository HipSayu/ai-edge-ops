from hopquangdo.messaging import PubSub, QoS

from src.shared.contracts import Command, EdgeTopics


class MqttCommandPublisher:
    """Publishes commands to `edge/{cluster_id}/{node_id}/command/{type}`."""

    def __init__(self, pubsub: PubSub) -> None:
        self._pubsub = pubsub

    async def send(self, cluster_id: str, node_id: str, command: Command) -> None:
        topic = EdgeTopics(cluster_id, node_id).command(command.type)
        await self._pubsub.publish(topic, command.model_dump(mode="json"), qos=QoS.AT_LEAST_ONCE)
