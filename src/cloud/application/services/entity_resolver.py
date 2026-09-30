"""Finds clusters, nodes, runtimes and deployments from what a person would type: an id, a code or a name.

Users (and the assistant speaking for them) know "Công trường A", "CT-A" or "Hố móng", not UUIDs. A reference
is matched in tiers and the first tier with any match wins:

    1. id            exact
    2. code          exact, ignoring case/diacritics  (cluster: metadata.site_code, node: metadata.code)
    3. name          exact, ignoring case/diacritics
    4. name contains the reference                   (only when `exact=False`, i.e. for reads)

One match -> that entity. Several -> INVALID_REQUEST listing the candidates, so the caller asks the user
instead of guessing. None -> NOT_FOUND with the closest names. Write tools pass `exact=True`: a partial
name never picks what gets changed.
"""

import unicodedata
from collections.abc import Callable, Sequence
from typing import TypeVar

from src.cloud.application.ports.cluster_repository import ClusterRepository
from src.cloud.application.ports.deployment_repository import DeploymentRepository
from src.cloud.application.ports.node_repository import NodeRepository
from src.cloud.application.ports.runtime_repository import RuntimeRepository
from src.cloud.domain.entities.cluster import Cluster
from src.cloud.domain.entities.deployment import Deployment
from src.cloud.domain.entities.node import Node
from src.cloud.domain.entities.runtime import Runtime
from src.shared.exceptions import AppException, ErrorCode

T = TypeVar("T")

# "CT-A/Hố móng": a node (or runtime) reference scoped by its cluster (or node)
SCOPE_SEPARATOR = "/"
MAX_CANDIDATES = 8


def normalize(text: str | None) -> str:
    """Lowercase, no diacritics (đ -> d), single spaces: "Hố  Móng" == "ho mong"."""
    text = (text or "").replace("đ", "d").replace("Đ", "D")
    stripped = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return " ".join(stripped.lower().split())


def match(
    ref: str, items: Sequence[T], *, id_of: Callable[[T], str], name_of: Callable[[T], str],
    code_of: Callable[[T], str | None] = lambda _: None, exact: bool = False,
) -> list[T]:
    """The items `ref` points at, from the first tier that matches anything (see module doc)."""
    ref = ref.strip()
    key = normalize(ref)
    tiers: list[Callable[[T], bool]] = [
        lambda item: id_of(item) == ref,
        lambda item: bool(code_of(item)) and normalize(code_of(item)) == key,
        lambda item: normalize(name_of(item)) == key,
    ]
    if not exact:
        tiers.append(lambda item: bool(key) and key in normalize(name_of(item)))
    for tier in tiers:
        found = [item for item in items if tier(item)]
        if found:
            return found
    return []


class EntityResolver:
    def __init__(
        self, clusters: ClusterRepository, nodes: NodeRepository, runtimes: RuntimeRepository,
        deployments: DeploymentRepository,
    ) -> None:
        self._clusters = clusters
        self._nodes = nodes
        self._runtimes = runtimes
        self._deployments = deployments

    async def cluster(self, ref: str, *, exact: bool = False) -> Cluster:
        clusters = await self._clusters.list()
        found = match(ref, clusters, id_of=lambda c: c.id, name_of=lambda c: c.name, code_of=cluster_code,
                      exact=exact)
        return self._one("cluster", ref, found, clusters, lambda c: c.name,
                         lambda c: cluster_code(c) or "")

    async def node(self, ref: str, *, cluster: str | None = None, exact: bool = False) -> Node:
        """`ref` may carry its cluster ("CT-A/Hố móng"); node names are unique only within a cluster."""
        scope, ref = self._split(ref, cluster)
        candidates = await self._nodes.list((await self.cluster(scope, exact=exact)).id if scope else None)
        found = match(ref, candidates, id_of=lambda n: n.id, name_of=lambda n: n.name, code_of=node_code,
                      exact=exact)
        names = await self._cluster_names()
        return self._one("node", ref, found, candidates, lambda n: n.name,
                         lambda n: node_code(n) or names.get(n.cluster_id, ""))

    async def nodes_in(self, cluster: str | None, *, exact: bool = False) -> list[Node]:
        """Every node, or those of one cluster."""
        return await self._nodes.list((await self.cluster(cluster, exact=exact)).id if cluster else None)

    async def runtime(
        self, ref: str, *, node: str | None = None, cluster: str | None = None, exact: bool = False
    ) -> Runtime:
        """A runtime by id, or by name ("ppe-detector") within a node ("Hố móng/ppe-detector")."""
        scope, ref = self._split(ref, node)
        if scope:
            candidates = await self._runtimes.list((await self.node(scope, cluster=cluster, exact=exact)).id)
        else:
            nodes = {n.id for n in await self.nodes_in(cluster, exact=exact)}
            candidates = [r for r in await self._runtimes.list() if r.node_id in nodes]
        found = match(ref, candidates, id_of=lambda r: r.id, name_of=lambda r: r.name, exact=exact)
        node_names = {n.id: n.name for n in await self._nodes.list()}
        return self._one("runtime", ref, found, candidates, lambda r: r.name,
                         lambda r: f"trên {node_names.get(r.node_id, r.node_id)}")

    async def deployment(
        self, ref: str, *, node: str | None = None, cluster: str | None = None, exact: bool = False
    ) -> Deployment:
        """A deployment by id, or by the name of the runtime it deploys (same scoping as `runtime`)."""
        deployment = await self._deployments.get(ref.strip())
        if deployment is not None:
            return deployment
        runtime = await self.runtime(ref, node=node, cluster=cluster, exact=exact)
        deployment = await self._deployments.get_by_runtime(runtime.id)
        if deployment is None:
            raise AppException(ErrorCode.NOT_FOUND, f"Runtime '{runtime.name}' không có deployment nào")
        return deployment

    async def _cluster_names(self) -> dict[str, str]:
        return {c.id: c.name for c in await self._clusters.list()}

    @staticmethod
    def _split(ref: str, scope: str | None) -> tuple[str | None, str]:
        if scope is None and SCOPE_SEPARATOR in ref:
            scope, _, ref = ref.rpartition(SCOPE_SEPARATOR)
            return scope.strip() or None, ref.strip()
        return scope, ref

    @staticmethod
    def _one(
        kind: str, ref: str, found: list[T], candidates: Sequence[T],
        name_of: Callable[[T], str], hint_of: Callable[[T], str],
    ) -> T:
        def label(item: T) -> str:
            hint = hint_of(item)
            return f"{name_of(item)} ({hint})" if hint else name_of(item)

        if len(found) == 1:
            return found[0]
        if found:
            options = ", ".join(label(item) for item in found[:MAX_CANDIDATES])
            raise AppException(
                ErrorCode.INVALID_REQUEST,
                f"'{ref}' khớp {len(found)} {kind}: {options}. Hỏi người dùng muốn chọn cái nào.",
                {"candidates": [name_of(item) for item in found]},
            )
        options = ", ".join(label(item) for item in candidates[:MAX_CANDIDATES])
        raise AppException(
            ErrorCode.NOT_FOUND,
            f"Không tìm thấy {kind} '{ref}'." + (f" Hiện có: {options}." if options else ""),
        )


def cluster_code(cluster: Cluster) -> str | None:
    return cluster.metadata.get("site_code") or cluster.metadata.get("code")


def node_code(node: Node) -> str | None:
    return node.metadata.get("code")
