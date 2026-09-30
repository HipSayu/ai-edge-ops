from typing import Protocol

from src.edge.domain.value_objects.node_info import NodeInfo


class NodeInfoProvider(Protocol):
    def info(self) -> NodeInfo: ...
