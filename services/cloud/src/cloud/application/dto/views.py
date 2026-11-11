"""What the adapters return (REST and MCP alike). Output shapes are built from domain objects and read models, so no
adapter ever touches a database row."""

import base64

from cloud.application.dto.read_models import CameraDetail, GridItem, NodeSummary, Stats
from cloud.domain.model.cluster import Cluster
from cloud.domain.violation.detection import DetectionResult
from cloud.domain.model.user import User
from cloud.domain.violation.violation_event import ViolationEvent


def detection_out(result: DetectionResult) -> dict:
    return {
        "detections": [{"label": o.label, "confidence": round(o.confidence, 3), "box": list(o.box)} for o in result.objects],
        "annotated_jpeg_b64": base64.b64encode(result.annotated_jpeg).decode("ascii"),
    }


def user_out(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active,
        "cluster_ids": sorted(user.cluster_ids),
    }


def cluster_out(cluster: Cluster) -> dict:
    return {"id": cluster.id, "name": cluster.name, "description": cluster.description}


def node_out(node: NodeSummary) -> dict:
    return {
        "id": node.id,
        "name": node.name,
        "cluster_id": node.cluster_id,
        "cluster_name": node.cluster_name,
        "description": node.description,
        "ip_address": node.ip_address,
        "max_cameras": node.max_cameras,
        "camera_count": node.camera_count,
    }


def camera_out(detail: CameraDetail) -> dict:
    row = detail.row
    return {
        "id": row.id,
        "name": row.name,
        "zone": row.zone,
        "enabled": row.enabled,
        "node_id": row.node_id,
        "node_name": row.node_name,
        "cluster_id": row.cluster_id,
        "cluster_name": row.cluster_name,
        "videos": detail.videos,
    }


def event_out(event: ViolationEvent) -> dict:
    return {
        "id": event.id,
        "camera_id": event.camera_id,
        "violation_type": event.violation_type,
        "confidence": event.confidence,
        "created_at": event.created_at.isoformat(),
    }


def grid_item_out(item: GridItem) -> dict:
    camera = item.camera
    return {
        "camera_id": camera.id,
        "name": camera.name,
        "zone": camera.zone,
        "node_id": camera.node_id,
        "node_name": camera.node_name,
        "cluster_id": camera.cluster_id,
        "cluster_name": camera.cluster_name,
        "person_count": item.person_count,
        "violation_count_recent": item.recent_violations,
        "score": item.score,
        "online": item.online,
        "stream_url": f"/api/cameras/{camera.id}/stream",
    }


def stats_out(stats: Stats) -> dict:
    return {"total": stats.total, "by_type": stats.by_type}
