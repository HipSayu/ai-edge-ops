"""Monitoring tools. `node` takes an id, a code or a name (see EntityResolver); `cluster` narrows it when
several clusters have a node with that name."""

from typing import Any, Literal

from apps.cloud.dependencies import get_monitoring, get_resolver
from apps.cloud.mcp_server.server import mcp


@mcp.tool()
async def get_latest_telemetry(node: str, cluster: str | None = None) -> dict[str, dict[str, Any]]:
    """Số liệu giám sát (telemetry) mới nhất của một node: tài nguyên hệ thống (CPU, RAM, nhiệt độ, đĩa, mạng),
    GPU, và từng runtime (FPS inference, độ trễ, camera, độ tin cậy). Khóa: system, gpu, runtime:<runtime_id>.
    node: tên, mã hoặc id của node."""
    found = await get_resolver().node(node, cluster=cluster)
    return await get_monitoring().latest(found.id)


@mcp.tool()
async def get_telemetry_history(
    node: str, kind: Literal["system", "gpu", "runtime"], cluster: str | None = None, limit: int = 100
) -> list[dict[str, Any]]:
    """Lịch sử telemetry của một node theo loại (kind: system, gpu hoặc runtime), mới nhất trước, tối đa 1 giờ gần
    nhất. Dùng để xem xu hướng theo thời gian (nhiệt độ, CPU, FPS tăng/giảm từ khi nào)."""
    found = await get_resolver().node(node, cluster=cluster)
    return await get_monitoring().history(found.id, kind, limit)


@mcp.tool()
async def get_node_events(node: str, cluster: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Nhật ký sự kiện gần đây của một node: lỗi, cảnh báo, thay đổi trạng thái runtime, kết quả lệnh
    deploy / update / restart. Dùng để tìm nguyên nhân và thời điểm sự cố."""
    found = await get_resolver().node(node, cluster=cluster)
    return await get_monitoring().events(found.id, limit)
