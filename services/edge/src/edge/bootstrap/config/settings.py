from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class CameraConfig(BaseModel):
    id: int  # the camera's id in the cloud service: events are filed under it
    uri: str  # rtsp://host/stream for a camera, or file:///path/video.mp4 (played in a loop) to stand in for one


class NodeConfig(BaseModel):
    node_id: str  # also the broker user name: a node may write only under its own id
    mqtt_password: str | None = None
    cameras: list[CameraConfig]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EDGE_", env_file=".env", extra="ignore")

    node_id: str | None = None  # names this device in the topics
    cameras: list[CameraConfig] = []  # as JSON in EDGE_CAMERAS, e.g. [{"id": 1, "uri": "rtsp://camera1/stream"}]
    # Or several nodes in one process, sharing one model (a mock fleet on one machine; a real device runs one node):
    # EDGE_NODES='[{"node_id": "edge-c1", "mqtt_password": "...", "cameras": [{"id": 53, "uri": "file:///videos/53.mp4"}]}]'
    nodes: list[NodeConfig] = []

    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_tls_ca: str | None = None  # CA certificate (PEM) of the broker: set it to talk TLS (port 8883)

    engine_path: Path = Path("weights/ppe_fp16.engine")  # a TensorRT engine built for this device, with a batch of at least the number of cameras
    precision: str = "fp16"  # which engine it is: fp16 or int8 (the engine decides; this only names it for DeepStream)
    class_names: tuple[str, ...] = ("person", "helmet", "no_helmet", "vest", "no_vest", "gloves", "no_gloves", "boots", "no_boots")
    infer_imgsz: int = 960
    conf: float = 0.35
    infer_interval: int = 0  # batches skipped between two inferences; the tracker carries the objects across them
    mux_width: int = 960  # the size every camera is scaled to before the model
    mux_height: int = 540
    mux_timeout_us: int = 66667  # how long the muxer waits for a late camera: about one frame at 15 fps
    unified_memory: bool = True  # lets the snapshot be read back on a discrete GPU; a Jetson does not need it
    reconnect_sec: int = 10  # a dropped camera is retried this often
    deepstream_dir: Path = Path("data/deepstream")  # where the property files DeepStream reads are written
    tracker_lib: str = "/opt/nvidia/deepstream/deepstream/lib/libnvds_nvmultiobjecttracker.so"
    tracker_config: str = "/opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/config_tracker_IOU.yml"
    event_cooldown_sec: float = 5.0  # per violation of one person once tracked, per label otherwise
    tracking: bool = True  # follow the objects with nvtracker so the cooldown and the confirmation are per person
    min_frames: int = 3  # sightings of a violation (detections, not camera frames) before it is reported
    forget_after_sec: float = 10.0  # a violation not seen for this long starts counting again
    publish_detections: bool = True  # send every box to the cloud so the web can draw them over the video
    outbox_path: Path = Path("data/outbox.db")  # events wait here, on disk, until the broker acknowledges them
    outbox_max_events: int = 500  # events kept while the cloud is unreachable; the oldest is dropped past this
    violation_classes: tuple[str, ...] = ("no_helmet", "no_vest", "no_gloves", "no_safety_boots")

    # Forbidden zones: drawn on the web, sent by the cloud over MQTT (retained), checked here against where each person stands
    zones_enabled: bool = True
    zones_path: Path = Path("data/zones.json")  # a copy on disk, so a restart with the cloud out of reach still has the zones
    zone_classes: tuple[str, ...] = ("person",)  # the detector labels that count as someone entering
    zone_cooldown_sec: float = 10.0  # while someone stays in a zone the alarm repeats at most this often
    # What sounds on the spot (all optional, all without the cloud): a log line always, plus a command and/or a URL
    alarm_command: list[str] = []  # an argument list as JSON, e.g. ["aplay", "/sounds/alarm.wav"]; gets PPE_ALARM_CAMERA and PPE_ALARM_ZONE
    alarm_url: str | None = None  # called with GET, {camera} and {zone} replaced: a siren on the site's network

    def node_configs(self) -> list[NodeConfig]:
        """The nodes this process runs: the `nodes` list, or the one node of node_id and cameras."""
        if self.nodes:
            return self.nodes
        if not self.node_id:
            raise ValueError("Set EDGE_NODE_ID and EDGE_CAMERAS, or EDGE_NODES")
        return [NodeConfig(node_id=self.node_id, mqtt_password=self.mqtt_password, cameras=self.cameras)]
