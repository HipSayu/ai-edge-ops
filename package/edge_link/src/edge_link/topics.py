"""The MQTT topics between the edge runtimes and the cloud.

  ppe/{node_id}/cameras/{camera_id}/events   one ViolationMessage (JSON) per violation
  ppe/{node_id}/cameras/{camera_id}/detections   every box of one detection (JSON), for the live overlay
  ppe/{node_id}/status                       "online" / "offline", retained ("offline" is the broker's last will)
  ppe/config/cameras/{camera_id}/zones       the forbidden zones of one camera (JSON), retained, cloud to edge
"""

QOS = 1  # at least once: the receiver drops a repeat by event_id
ONLINE, OFFLINE = "online", "offline"
QOS_DETECTIONS = 0  # a lost set of boxes is replaced by the next one, a few times a second
EVENTS_FILTER = "ppe/+/cameras/+/events"  # what the cloud subscribes to
DETECTIONS_FILTER = "ppe/+/cameras/+/detections"


def events_topic(node_id: str, camera_id: int) -> str:
    return f"ppe/{node_id}/cameras/{camera_id}/events"


def detections_topic(node_id: str, camera_id: int) -> str:
    return f"ppe/{node_id}/cameras/{camera_id}/detections"


def status_topic(node_id: str) -> str:
    return f"ppe/{node_id}/status"


# The zones of a camera (where no one may enter), written by the cloud, read by the node that runs the camera.
# Retained: a node that starts, or comes back after an outage, is told the current zones at once.
ZONES_QOS = 1
ZONES_PREFIX = "ppe/config/cameras"


def zones_topic(camera_id: int) -> str:
    return f"{ZONES_PREFIX}/{camera_id}/zones"
