"""What one node's DeepStream pipeline is built from, and how it is made from the node's settings."""

from dataclasses import dataclass, field
from pathlib import Path

from edge.bootstrap.config.settings import Settings


@dataclass(frozen=True)
class CameraSource:
    camera_id: int
    uri: str  # rtsp://..., file:///..., or a device the nvurisrcbin knows

    @property
    def live(self) -> bool:
        return self.uri.startswith(("rtsp://", "rtsps://", "http://", "https://"))


@dataclass(frozen=True)
class DeepStreamConfig:
    cameras: tuple[CameraSource, ...]
    engine_path: Path
    class_names: tuple[str, ...]
    precision: str = "fp16"
    net_size: int = 960
    conf: float = 0.35
    interval: int = 0  # batches skipped between two inferences (the tracker carries the objects across them)
    mux_width: int = 960
    mux_height: int = 540
    mux_timeout_us: int = 66667  # how long the muxer waits for a late camera before sending the batch it has: about one frame at 15 fps
    tracking: bool = True
    tracker_lib: str = "/opt/nvidia/deepstream/deepstream/lib/libnvds_nvmultiobjecttracker.so"
    tracker_config: str = "/opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/config_tracker_IOU.yml"
    tracker_width: int = 640
    tracker_height: int = 384
    unified_memory: bool = True  # lets the snapshot be read back to the CPU on a discrete GPU (not needed on a Jetson)
    work_dir: Path = Path("data/deepstream")
    reconnect_sec: int = 10  # a camera that drops is retried this often
    sync: bool = False  # play at the sources' own pace (a file standing in for a camera); a live camera paces itself
    drop_frame_interval: int = 0  # the decoder passes on one frame in this many (0: all); 2 turns a 30 fps camera into 15
    extra: dict = field(default_factory=dict)

    @property
    def batch_size(self) -> int:
        return len(self.cameras)


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
