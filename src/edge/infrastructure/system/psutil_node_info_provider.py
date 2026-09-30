import socket

import psutil

from src.edge.domain.value_objects.node_info import NodeInfo


class PsutilNodeInfoProvider:
    def __init__(self, gpu_name: str | None = None) -> None:
        self._gpu_name = gpu_name

    def info(self) -> NodeInfo:
        return NodeInfo(
            hostname=socket.gethostname(),
            ip_address=self._primary_ip(),
            cpu_cores=psutil.cpu_count(logical=True),
            memory_total_mb=int(psutil.virtual_memory().total / 2**20),
            gpu_name=self._gpu_name,
        )

    @staticmethod
    def _primary_ip() -> str | None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("10.255.255.255", 1))
                return s.getsockname()[0]
        except OSError:
            return None
