from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class CameraConfig(BaseModel):
    id: int  # the camera's id in the cloud service: events are filed under it
    video: Path  # a video file, or a folder of them, played in a loop (stands in for a live camera)


class NodeConfig(BaseModel):
    node_id: str  # also the broker user name: a node may write only under its own id
    mqtt_password: str | None = None
    cameras: list[CameraConfig]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EDGE_", env_file=".env", extra="ignore")

    node_id: str | None = None  # names this device in the topics
    cameras: list[CameraConfig] = []  # as JSON in EDGE_CAMERAS, e.g. [{"id": 1, "video": "videos/cam1"}]
    # Or several nodes in one process, sharing one model (a mock fleet on one machine; a real device runs one node):
    # EDGE_NODES='[{"node_id": "edge-c1", "mqtt_password": "...", "cameras": [{"id": 53, "video": "/videos/4/22/53"}]}]'
    nodes: list[NodeConfig] = []

    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_tls_ca: str | None = None  # CA certificate (PEM) of the broker: set it to talk TLS (port 8883)

    model_path: Path = Path("weights/ppe.pt")
    infer_imgsz: int = 960
    device: str = "cpu"  # where the model runs: "cpu", or "cuda:0" on a GPU build of the image
    conf: float = 0.35
    batch_max: int = 8  # frames of different cameras looked at in one model call (a GPU does eight in little more time than one)
    batch_gather_ms: float = 4.0  # how long a call waits for more frames once it has one
    infer_every_n_frames: int = 1  # at most one detection per this many frames of a camera
    video_max_fps: float = 30.0  # caps how fast a video file is decoded; lower it on an underpowered host
    torch_threads: int = 1  # threads inside one inference; cameras run in parallel on top of that
    event_cooldown_sec: float = 5.0  # per violation of one person once tracked, per label otherwise
    tracking: bool = True  # follow each violation with ByteTrack so the cooldown and the confirmation are per person
    track_buffer: int = 90  # detections a lost track is kept for before it is dropped
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
