"""Fleet tools. Every reference parameter (`cluster`, `node`, `runtime`) takes an id, a code or a name, the way
the user said it ("Công trường A", "CT-A", "Hố móng"): see EntityResolver. Reads accept a partial name, writes
need an exact one."""

from typing import Any

from apps.cloud.dependencies import get_fleet, get_monitoring, get_resolver
from apps.cloud.mcp_server.server import mcp
from apps.cloud.mcp_server.views import Directory, cluster_view, node_view, runtime_view
from src.cloud.application.services.entity_resolver import normalize
from src.shared.contracts import NodeStatus, RuntimeStatus

OVERVIEW_EVENTS = 10


@mcp.tool()
async def list_clusters(query: str | None = None) -> list[dict[str, Any]]:
    """Liệt kê các cluster (công trường, site, khu vực) kèm mã, trạng thái, vị trí, mô tả và số node theo trạng thái.
    query: lọc theo tên/mã/vị trí (không cần dấu)."""
    fleet = get_fleet()
    nodes = await fleet.list_nodes()
    clusters = await fleet.list_clusters()
    if query:
        key = normalize(query)
        clusters = [c for c in clusters if key in normalize(f"{c.name} {c.location} {c.metadata.get('site_code')}")]
    return [cluster_view(c, [n for n in nodes if n.cluster_id == c.id]) for c in clusters]


@mcp.tool()
async def get_cluster(cluster: str) -> dict[str, Any]:
    """Chi tiết một cluster (công trường): tên, mã, vị trí, mô tả, metadata, trạng thái và danh sách node.
    cluster: tên, mã (vd CT-A) hoặc id."""
    found = await get_resolver().cluster(cluster)
    directory = await Directory.load(get_fleet())
    nodes = [n for n in directory.nodes.values() if n.cluster_id == found.id]
    return {**cluster_view(found, nodes), "node_list": [node_view(n, directory) for n in nodes]}


@mcp.tool()
async def create_cluster(
    name: str, description: str | None = None, location: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Tạo cluster (công trường, site) mới để chứa các edge node. Lỗi nếu tên đã tồn tại.
    metadata nên có site_code (mã ngắn, vd CT-E). Thay đổi hệ thống: mỗi lần gọi đều chờ người dùng duyệt."""
    return cluster_view(await get_fleet().create_cluster(name, description, location, metadata))


@mcp.tool()
async def list_nodes(
    cluster: str | None = None, status: NodeStatus | None = None, query: str | None = None
) -> list[dict[str, Any]]:
    """Liệt kê edge node (thiết bị biên, máy Jetson) kèm cluster, trạng thái ONLINE / OFFLINE / DEGRADED và heartbeat
    gần nhất. Lọc: cluster (tên/mã/id), status, query (một phần tên/mã node, không cần dấu)."""
    resolver = get_resolver()
    nodes = await resolver.nodes_in(cluster)
    if status:
        nodes = [n for n in nodes if n.status == status]
    if query:
        key = normalize(query)
        nodes = [n for n in nodes if key in normalize(f"{n.name} {n.metadata.get('code')}")]
    directory = await Directory.load(get_fleet())
    return [node_view(n, directory) for n in nodes]


@mcp.tool()
async def get_node(node: str, cluster: str | None = None) -> dict[str, Any]:
    """Chi tiết một edge node: trạng thái, heartbeat, phiên bản agent, phần cứng (CPU, RAM, GPU), metadata.
    node: tên, mã hoặc id; có thể ghi kèm cluster "CT-A/Hố móng" hoặc truyền cluster khi tên trùng."""
    found = await get_resolver().node(node, cluster=cluster)
    return node_view(found, await Directory.load(get_fleet()))


@mcp.tool()
async def get_node_overview(node: str, cluster: str | None = None) -> dict[str, Any]:
    """Tổng quan một node trong 1 lần gọi: thông tin node, telemetry mới nhất (CPU, RAM, nhiệt độ, GPU, FPS từng
    runtime), các runtime đang chạy và sự kiện gần đây. Dùng trước tiên khi hỏi tình trạng / sự cố của một node."""
    found = await get_resolver().node(node, cluster=cluster)
    fleet, monitoring = get_fleet(), get_monitoring()
    directory = await Directory.load(fleet)
    runtimes = [runtime_view(r, directory) for r in await fleet.list_runtimes(found.id)]
    telemetry = await monitoring.latest(found.id)
    # Telemetry keys runtimes by id ("runtime:<id>"): show the runtime name instead
    telemetry = {
        f"runtime:{directory.runtimes[k.split(':', 1)[1]].name}" if k.startswith("runtime:")
        and k.split(":", 1)[1] in directory.runtimes else k: v
        for k, v in telemetry.items()
    }
    return {
        "node": node_view(found, directory),
        "telemetry": telemetry,
        "runtimes": runtimes,
        "recent_events": await monitoring.events(found.id, OVERVIEW_EVENTS),
    }


@mcp.tool()
async def register_node(cluster: str, name: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Đăng ký edge node mới vào một cluster (tên/mã/id chính xác); trả về node_id để cấu hình agent trên máy.
    metadata nên có code (mã node, vd CT-A-04). Lỗi nếu tên đã có trong cluster đó.
    Thay đổi hệ thống: mỗi lần gọi đều chờ người dùng duyệt."""
    target = await get_resolver().cluster(cluster, exact=True)
    created = await get_fleet().register_node(target.id, name, metadata)
    return node_view(created, await Directory.load(get_fleet()))


@mcp.tool()
async def list_runtimes(
    node: str | None = None, cluster: str | None = None, status: RuntimeStatus | None = None
) -> list[dict[str, Any]]:
    """Liệt kê runtime (container model AI đang chạy, vd model PPE) kèm node, cluster, trạng thái RUNNING / FAILED /
    STOPPED và image. Lọc: node (tên/mã/id), cluster, status. Dùng để xem máy chạy model gì hoặc runtime nào lỗi."""
    resolver, fleet = get_resolver(), get_fleet()
    if node:
        runtimes = await fleet.list_runtimes((await resolver.node(node, cluster=cluster)).id)
    else:
        node_ids = {n.id for n in await resolver.nodes_in(cluster)}
        runtimes = [r for r in await fleet.list_runtimes() if r.node_id in node_ids]
    if status:
        runtimes = [r for r in runtimes if r.status == status]
    directory = await Directory.load(fleet)
    return [runtime_view(r, directory) for r in runtimes]


@mcp.tool()
async def get_runtime(runtime: str, node: str | None = None, cluster: str | None = None) -> dict[str, Any]:
    """Chi tiết một runtime: trạng thái, image, model, config, node, thời điểm khởi động.
    runtime: tên (vd ppe-detector) hoặc id; truyền node (hoặc ghi "Hố móng/ppe-detector") khi nhiều node cùng tên."""
    found = await get_resolver().runtime(runtime, node=node, cluster=cluster)
    return runtime_view(found, await Directory.load(get_fleet()))
