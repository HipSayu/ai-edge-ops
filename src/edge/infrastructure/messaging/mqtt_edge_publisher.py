from hopquangdo.messaging import PubSub, QoS
from pydantic import BaseModel

from src.shared.contracts import EdgeEvent, EdgeTopics, NodeState, RuntimeLogBatch


class MqttEdgePublisher:
    """Publishes this node's state, telemetry and events on its `edge/{cluster}/{node}/...` topics."""

    def __init__(self, pubsub: PubSub, topics: EdgeTopics) -> None:
        self._pubsub = pubsub
        self.topics = topics

    async def state(self, state: NodeState) -> None:
        payload = state.model_dump(mode="json")
        await self._pubsub.publish(self.topics.state(), payload, qos=QoS.AT_LEAST_ONCE, retain=True)
        runtimes = {"node_id": state.node_id, "runtimes": payload["runtimes"], "timestamp": payload["timestamp"]}
        await self._pubsub.publish(self.topics.runtime_state(), runtimes, qos=QoS.AT_LEAST_ONCE, retain=True)

    async def telemetry(self, kind: str, sample: BaseModel) -> None:
        payload = sample.model_dump(mode="json", exclude_none=True)
        await self._pubsub.publish(self.topics.telemetry(kind), payload, qos=QoS.AT_MOST_ONCE)

    async def event(self, kind: str, event: EdgeEvent) -> None:
        await self._pubsub.publish(self.topics.event(kind), event.model_dump(mode="json"), qos=QoS.AT_LEAST_ONCE)

    async def logs(self, batch: RuntimeLogBatch) -> None:
        # Best effort like telemetry: a lost batch only leaves a gap in the log view
        await self._pubsub.publish(self.topics.logs(batch.runtime_id), batch.model_dump(mode="json"), qos=QoS.AT_MOST_ONCE)
