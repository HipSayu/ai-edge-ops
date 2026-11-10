"""What one node's DeepStream pipeline is built from, and the property file `nvinfer` reads."""

from dataclasses import dataclass, field
from pathlib import Path

_NETWORK_MODE = {"fp32": 0, "int8": 1, "fp16": 2}  # nvinfer's network-mode; only informative for an engine that is already built
PGIE_ID = 1  # the unique id of the detector (gie-unique-id)
NO_TRACK = 0xFFFFFFFFFFFFFFFF  # the object id DeepStream gives to an object no tracker has followed


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
    mux_width: int = 1280
    mux_height: int = 720
    mux_timeout_us: int = 66667  # how long the muxer waits for a late camera before sending the batch it has: about one frame at 15 fps
    tracking: bool = True
    tracker_lib: str = "/opt/nvidia/deepstream/deepstream/lib/libnvds_nvmultiobjecttracker.so"
    tracker_config: str = "/opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/config_tracker_IOU.yml"
    tracker_width: int = 640
    tracker_height: int = 384
    unified_memory: bool = True  # lets the snapshot be read back to the CPU on a discrete GPU (not needed on a Jetson)
    work_dir: Path = Path("data/deepstream")
    reconnect_sec: int = 10  # a camera that drops is retried this often
    extra: dict = field(default_factory=dict)

    @property
    def batch_size(self) -> int:
        return len(self.cameras)


def nvinfer_properties(cfg: DeepStreamConfig) -> str:
    """The property file of the detector: the prebuilt engine, its input, and 'no post-processing, give me the tensor'."""
    mode = _NETWORK_MODE.get(cfg.precision.lower())
    if mode is None:
        raise ValueError(f"unknown precision {cfg.precision!r}: use fp32, fp16 or int8")
    return "\n".join([
        "[property]",
        "gpu-id=0",
        "net-scale-factor=0.0039215697906911373",
        "model-color-format=0",  # RGB
        f"model-engine-file={Path(cfg.engine_path).resolve().as_posix()}",
        f"batch-size={cfg.batch_size}",
        f"network-mode={mode}",
        f"num-detected-classes={len(cfg.class_names)}",
        f"interval={cfg.interval}",
        f"gie-unique-id={PGIE_ID}",
        "process-mode=1",
        "network-type=100",  # other: DeepStream does not decode the output, parser.py does
        "output-tensor-meta=1",
        "maintain-aspect-ratio=1",
        "symmetric-padding=1",
        "cluster-mode=4",
        "",
    ])
