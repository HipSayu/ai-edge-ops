"""The PPE tools: plain internal operations on the cloud use cases, one function each, with no protocol in sight.
The first two arguments are the container and the caller; the rest are the tool's inputs, and the docstring is what the
model reads. Reads are open to any signed-in viewer (the use cases apply their scope); changes are ADMIN-only.
An adapter (cloud/interface/mcp) publishes every tool in TOOLS to everyone (the role is checked when one is called)
and says which ones change data: the client (the assistant) asks its user before running those."""

import inspect
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

from cloud.application.usecases.chat_files_service import IMAGE_URL_PREFIX
from cloud.application.dto.views import camera_out, cluster_out, node_out, user_out
from cloud.bootstrap.container import Container
from shared.roles import Role
from shared.viewer import Viewer


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    run: Callable[..., Any]  # (container, viewer, **inputs)
    minimum: Role | None
    changes: bool = False  # True: writes data, so a client should have the user confirm it


TOOLS: list[Tool] = []


def tool(minimum: Role | None = None, *, changes: bool = False) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def register(fn: Callable[..., Any]) -> Callable[..., Any]:
        TOOLS.append(Tool(fn.__name__, inspect.getdoc(fn) or "", fn, minimum, changes))
        return fn

    return register


# --- reads


@tool()
def list_clusters(c: Container, v: Viewer) -> Any:
    """Clusters (construction sites) the caller may access."""
    return [cluster_out(x) for x in c.catalog.clusters(v)]


@tool()
def list_nodes(c: Container, v: Viewer) -> Any:
    """Nodes (edge devices) the caller may access, with camera counts and capacity."""
    return [node_out(x) for x in c.catalog.nodes(v, None)]


@tool()
def list_cameras(c: Container, v: Viewer) -> Any:
    """Cameras the caller may access, with node, cluster and videos."""
    return [camera_out(x) for x in c.catalog.camera_details(v)]


@tool()
def camera_status(c: Container, v: Viewer, camera_id: int) -> Any:
    """Live status of one camera: people now, violations in the last 10 minutes, videos."""
    return asdict(c.catalog.camera_status(v, camera_id))


@tool(Role.ADMIN)
def list_users(c: Container, v: Viewer) -> Any:
    """User accounts with role and clusters. ADMIN only."""
    return [user_out(u) for u in c.users.all()]


@tool()
def find_violations(
    c: Container, v: Viewer, since_minutes: int = 60, camera_id: int | None = None, cluster_id: int | None = None,
    violation_type: str | None = None, limit: int = 10,
) -> Any:
    """PPE violations in a time window: total, by type, by camera, latest events."""
    return asdict(c.violations.find(v, since_minutes, camera_id, cluster_id, violation_type, limit))


@tool()
def violation_frame(c: Container, v: Viewer, event_id: int) -> Any:
    """Frame details of one violation event, with the link of its saved image."""
    return {**c.violations.frame(v, event_id), "image_url": f"/api/snapshots/{event_id}"}


@tool()
def violation_trend(
    c: Container, v: Viewer, hours: int = 24, bucket: str = "hour", cluster_id: int | None = None,
    camera_id: int | None = None,
) -> Any:
    """Violation counts over time, grouped by hour or day."""
    return c.analytics.trend(v, hours, bucket, cluster_id, camera_id)


@tool()
def rank_violations(
    c: Container, v: Viewer, by: str = "camera", since_minutes: int = 60, cluster_id: int | None = None, limit: int = 5,
) -> Any:
    """Top cameras, nodes, clusters or violation types by number of violations."""
    return c.analytics.rank(v, by, since_minutes, cluster_id, limit)


@tool()
def compare_periods(c: Container, v: Viewer, window_minutes: int = 60, cluster_id: int | None = None) -> Any:
    """Last window of violations against the window right before it."""
    return c.violations.compare(v, window_minutes, cluster_id)


# --- changes: ADMIN only. The assistant runs them only after its user confirmed


@tool(Role.ADMIN, changes=True)
def create_cluster(c: Container, v: Viewer, name: str, description: str | None = None) -> Any:
    """Create a cluster (construction site)."""
    return cluster_out(c.clusters.create(name, description))


@tool(Role.ADMIN, changes=True)
def create_node(
    c: Container, v: Viewer, cluster_id: int, name: str, max_cameras: int = 16,
    description: str | None = None, ip_address: str | None = None,
) -> Any:
    """Create a node in a cluster."""
    return node_out(c.nodes.create(
        name=name, cluster_id=cluster_id, max_cameras=max_cameras, description=description, ip_address=ip_address,
    ))


@tool(Role.ADMIN, changes=True)
def delete_node(c: Container, v: Viewer, node_id: int) -> Any:
    """Delete a node and its cameras. Video files stay on disk."""
    return c.nodes.delete(node_id)


@tool(Role.ADMIN, changes=True)
def create_camera(c: Container, v: Viewer, node_id: int, name: str, zone: str | None = None, enabled: bool = True) -> Any:
    """Add a camera to a node."""
    return camera_out(c.cameras.create(node_id, name, zone, enabled))


@tool(Role.ADMIN, changes=True)
def update_camera(c: Container, v: Viewer, camera_id: int, name: str, zone: str | None = None, enabled: bool = True) -> Any:
    """Change a camera's name, zone or enabled flag."""
    return camera_out(c.cameras.update(camera_id, name=name, zone=zone, enabled=enabled))


@tool(Role.ADMIN, changes=True)
def delete_camera(c: Container, v: Viewer, camera_id: int) -> Any:
    """Delete a camera. Its video files stay on disk."""
    return c.cameras.delete(camera_id)


# --- the assistant's own: regulations, attached pictures and reports


@tool()
def search_knowledge(c: Container, v: Viewer, query: str, top_k: int = 3) -> Any:
    """Search the knowledge base: the documents provided by the customer (safety regulations and standards). Returns the
    best matching passages with their source file and section."""
    return c.knowledge.search(query, top_k)


@tool()
def detect_ppe(c: Container, v: Viewer, image_id: str) -> Any:
    """Run the PPE detection model on a picture the user attached (image_id) and return what it found: people, helmets,
    vests, gloves, boots and the missing ones (labels starting with no_), with the picture marked with boxes. Call it for
    every attached picture before answering about it."""
    seen = c.chat_images.look(v, image_id)
    counts = Counter(o.label for o in seen.objects)
    violations = [o for o in seen.objects if o.label.startswith("no_")]
    lines = [f"- {label}: {count}" for label, count in sorted(counts.items())] or ["- nothing detected"]
    verdict = (
        f"{len(violations)} violation(s): " + ", ".join(sorted({o.label for o in violations}))
        if violations else "no violation found"
    )
    return (
        f"Detected objects ({len(seen.objects)}):\n" + "\n".join(lines) + f"\nResult: {verdict}\n"
        f"Marked picture, to show in the reply as markdown: ![Kết quả nhận diện]({IMAGE_URL_PREFIX}{seen.annotated_id})"
    )


@tool()
def export_safety_report(c: Container, v: Viewer, title: str, body_markdown: str) -> Any:
    """Save a finished safety report as a Word (.docx) file and return its download link. Call it once, with the complete
    text."""
    return {"url": c.reports.export(v, title, body_markdown)}
