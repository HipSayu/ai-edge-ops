"""From the node's settings to what its DeepStream pipeline is built with."""

from edge.bootstrap.config.settings import Settings
from edge.infrastructure.deepstream.config import CameraSource, DeepStreamConfig


def deepstream_config(settings: Settings, node_id: str, cameras: list[CameraSource], several_nodes: bool) -> DeepStreamConfig:
    """One node's pipeline: its cameras (and so its batch size) and the engine, from the settings."""
    return DeepStreamConfig(
        cameras=tuple(cameras), engine_path=settings.engine_path, class_names=settings.class_names,
        precision=settings.precision, net_size=settings.infer_imgsz, conf=settings.conf, interval=settings.infer_interval,
        mux_width=settings.mux_width, mux_height=settings.mux_height, mux_timeout_us=settings.mux_timeout_us,
        tracking=settings.tracking, tracker_lib=settings.tracker_lib, tracker_config=settings.tracker_config,
        unified_memory=settings.unified_memory, reconnect_sec=settings.reconnect_sec,
        work_dir=settings.deepstream_dir / node_id if several_nodes else settings.deepstream_dir,
    )
