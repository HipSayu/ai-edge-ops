"""Telemetry schemas. Field names follow docs/design/telemetry-features.md exactly;
every metric is optional so devices report what they can measure."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.shared.contracts.enums import CameraStatus, NodeStatus, RuntimeStatus
from src.shared.domain.clock import Clock


class TelemetryBase(BaseModel):
    timestamp: datetime = Field(default_factory=Clock.now)
    node_id: str


class SystemTelemetry(TelemetryBase):
    """`telemetry/system` — node resource, thermal, power, storage, network, availability."""

    # CPU
    cpu_usage_pct: float | None = None
    cpu_load_1m: float | None = None
    cpu_load_5m: float | None = None
    cpu_iowait_pct: float | None = None
    cpu_context_switches: float | None = None
    # Memory
    memory_usage_pct: float | None = None
    memory_available_mb: float | None = None
    memory_used_mb: float | None = None
    swap_usage_pct: float | None = None
    memory_growth_rate: float | None = None
    # Thermal
    temperature_c: float | None = None
    cpu_temperature_c: float | None = None
    temperature_rate: float | None = None
    thermal_throttling: bool | None = None
    # Power
    power_w: float | None = None
    power_rate: float | None = None
    power_limit_w: float | None = None
    power_throttling: bool | None = None
    # Storage
    disk_usage_pct: float | None = None
    disk_free_gb: float | None = None
    inode_usage_pct: float | None = None
    disk_read_mb_s: float | None = None
    disk_write_mb_s: float | None = None
    disk_io_wait_pct: float | None = None
    # Network
    network_rtt_ms: float | None = None
    packet_loss_pct: float | None = None
    network_rx_mb_s: float | None = None
    network_tx_mb_s: float | None = None
    connection_reconnect_count: int | None = None
    mqtt_publish_latency_ms: float | None = None
    telemetry_queue_size: int | None = None
    # Availability
    node_uptime_sec: float | None = None
    reboot_count: int | None = None
    process_count: int | None = None
    agent_status: NodeStatus | None = None


class GpuTelemetry(TelemetryBase):
    """`telemetry/gpu` — GPU/NPU accelerator."""

    gpu_usage_pct: float | None = None
    gpu_memory_usage_pct: float | None = None
    gpu_memory_used_mb: float | None = None
    gpu_frequency_mhz: float | None = None
    gpu_power_w: float | None = None
    gpu_temperature_c: float | None = None


class RuntimeTelemetry(TelemetryBase):
    """`telemetry/runtime` — runtime, inference performance, camera and model output."""

    runtime_id: str
    # Runtime
    runtime_cpu_pct: float | None = None
    runtime_memory_mb: float | None = None
    runtime_restart_count: int | None = None
    runtime_uptime_sec: float | None = None
    runtime_error_rate: float | None = None
    runtime_error_count: int | None = None  # errors since the previous sample
    runtime_queue_size: int | None = None
    runtime_status: RuntimeStatus | None = None
    # Inference
    inference_fps: float | None = None
    target_fps: float | None = None
    effective_fps_ratio: float | None = None
    inference_latency_ms: float | None = None
    inference_p50_ms: float | None = None
    inference_p95_ms: float | None = None
    inference_p99_ms: float | None = None
    inference_error_rate: float | None = None
    inference_timeout_rate: float | None = None
    # Camera / sensor
    camera_fps: float | None = None
    camera_target_fps: float | None = None
    camera_frame_age_ms: float | None = None
    camera_frame_drop_pct: float | None = None
    camera_freeze_duration_sec: float | None = None
    camera_brightness: float | None = None
    camera_blur_score: float | None = None
    camera_status: CameraStatus | None = None
    # Model output
    detection_count: int | None = None
    confidence_mean: float | None = None
    confidence_std: float | None = None
    confidence_min: float | None = None
    class_entropy: float | None = None
    unknown_detection_rate: float | None = None
    output_change_rate: float | None = None
