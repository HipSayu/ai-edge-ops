from typing import Protocol

from src.shared.contracts import Command


class CommandPublisher(Protocol):
    """Delivers a command to one edge node (MQTT today)."""

    async def send(self, cluster_id: str, node_id: str, command: Command) -> None: ...
