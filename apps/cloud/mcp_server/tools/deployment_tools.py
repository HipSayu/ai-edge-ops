"""Deployment tools. A deployment is named after the runtime it deploys, so `deployment` takes that name
(vd "ppe-detector"), scoped by `node` / `cluster` when several nodes run one with the same name, or an id.
Every tool here changes the fleet, so references must match exactly (no partial names)."""

from typing import Any, Literal

from apps.cloud.dependencies import get_deployment_service, get_fleet, get_resolver
from apps.cloud.mcp_server.server import mcp
from apps.cloud.mcp_server.views import Directory, deployment_view
from src.cloud.application.dto.deployment_request import DeploymentRequest
from src.cloud.application.dto.deployment_update import DeploymentUpdate
from src.cloud.domain.entities.deployment import Deployment
from src.shared.contracts import CommandType, DeploymentStatus, RuntimeType


async def _view(deployment: Deployment) -> dict[str, Any]:
    return deployment_view(deployment, await Directory.load(get_fleet()))


@mcp.tool()
async def list_deployments(
    node: str | None = None, cluster: str | None = None, status: DeploymentStatus | None = None
) -> list[dict[str, Any]]:
    """Liệt kê deployment (lần triển khai runtime lên node) kèm node, cluster, image và trạng thái PENDING /
    IN_PROGRESS / SUCCEEDED / FAILED. Lọc: node (tên/mã/id), cluster, status. Dùng để xem đã deploy gì ở đâu."""
    resolver = get_resolver()
    if node:
        node_ids = {(await resolver.node(node, cluster=cluster)).id}
    else:
        node_ids = {n.id for n in await resolver.nodes_in(cluster)}
    deployments = [d for d in await get_deployment_service().list() if d.node_id in node_ids]
    if status:
        deployments = [d for d in deployments if d.status == status]
    directory = await Directory.load(get_fleet())
    return [deployment_view(d, directory) for d in deployments]


@mcp.tool()
async def get_deployment(deployment: str, node: str | None = None, cluster: str | None = None) -> dict[str, Any]:
    """Chi tiết một deployment: image, model, config, giới hạn tài nguyên, trạng thái và thông báo lỗi. Dùng để theo
    dõi kết quả deploy / update. deployment: tên runtime (vd ppe-detector) hoặc id; node/cluster khi tên trùng."""
    return await _view(await get_resolver().deployment(deployment, node=node, cluster=cluster))


@mcp.tool()
async def create_deployment(
    node: str, name: str, image_uri: str, cluster: str | None = None,
    type: RuntimeType = RuntimeType.VISION, image_tag: str = "latest",
    model_id: str | None = None, model_uri: str | None = None,
    config: dict[str, Any] | None = None, environment: dict[str, str] | None = None,
    resource_limits: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Triển khai (deploy) một runtime mới (image Docker chạy model AI) lên một edge node.
    node: tên/mã/id chính xác của node (cluster khi tên trùng); name: tên runtime (vd ppe-detector).
    Node báo kết quả sau vài giây đến vài phút: theo dõi bằng get_deployment.
    Thay đổi hệ thống: mỗi lần gọi đều chờ người dùng duyệt."""
    target = await get_resolver().node(node, cluster=cluster, exact=True)
    request = DeploymentRequest(
        node_id=target.id, name=name, type=type, image_uri=image_uri, image_tag=image_tag,
        model_id=model_id, model_uri=model_uri, config=config or {},
        environment=environment or {}, resource_limits=resource_limits or {},
    )
    return await _view(await get_deployment_service().create(request))


@mcp.tool()
async def update_deployment(
    deployment: str, node: str | None = None, cluster: str | None = None,
    image_uri: str | None = None, image_tag: str | None = None,
    model_id: str | None = None, model_uri: str | None = None,
    config: dict[str, Any] | None = None, environment: dict[str, str] | None = None,
    resource_limits: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Cập nhật deployment đang chạy: đổi image/tag, model, config (vd target_fps), biến môi trường hoặc giới hạn tài
    nguyên; chỉ các trường được truyền mới thay đổi. Cũng dùng để rollback về cấu hình cũ.
    deployment: tên runtime chính xác hoặc id; node/cluster khi nhiều node có runtime cùng tên.
    Thay đổi hệ thống: mỗi lần gọi đều chờ người dùng duyệt."""
    target = await get_resolver().deployment(deployment, node=node, cluster=cluster, exact=True)
    patch = DeploymentUpdate(
        image_uri=image_uri, image_tag=image_tag, model_id=model_id, model_uri=model_uri,
        config=config, environment=environment, resource_limits=resource_limits,
    )
    return await _view(await get_deployment_service().update(target.id, patch))


@mcp.tool()
async def remove_deployment(deployment: str, node: str | None = None, cluster: str | None = None) -> dict[str, Any]:
    """Gỡ (xóa) một deployment: dừng và xóa runtime của nó trên edge node. Không hoàn tác được.
    deployment: tên runtime chính xác hoặc id; node/cluster khi tên trùng.
    Thay đổi hệ thống: mỗi lần gọi đều chờ người dùng duyệt."""
    target = await get_resolver().deployment(deployment, node=node, cluster=cluster, exact=True)
    return await _view(await get_deployment_service().remove(target.id))


@mcp.tool()
async def control_runtime(
    runtime: str, action: Literal["start", "stop", "restart"], node: str | None = None, cluster: str | None = None
) -> dict[str, Any]:
    """Bật (start), dừng (stop) hoặc khởi động lại (restart) một runtime trên edge node.
    runtime: tên chính xác (vd ppe-detector) hoặc id; node/cluster khi nhiều node có runtime cùng tên.
    Thay đổi hệ thống: mỗi lần gọi đều chờ người dùng duyệt."""
    target = await get_resolver().runtime(runtime, node=node, cluster=cluster, exact=True)
    return await _view(await get_deployment_service().control_runtime(target.id, CommandType(action)))
