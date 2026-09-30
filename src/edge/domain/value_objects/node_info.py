from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NodeInfo:
    hostname: str | None = None
    ip_address: str | None = None
    cpu_cores: int | None = None
    memory_total_mb: int | None = None
    gpu_name: str | None = None
