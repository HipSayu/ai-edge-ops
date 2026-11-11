"""Numbers over violation events: trend, ranking, period comparison. Scoped to the viewer."""

from collections import Counter
from datetime import UTC, datetime, timedelta

from cloud.application.dto.scope import visible_cameras
from cloud.application.unit_of_work import UnitOfWorkFactory
from shared.errors import Invalid
from shared.viewer import Viewer

RANK_BY = ("camera", "node", "cluster", "type")


class AnalyticsService:
    def __init__(self, uow: UnitOfWorkFactory) -> None:
        self._uow = uow

    def trend(self, viewer: Viewer, hours: int = 24, bucket: str = "hour",
              cluster_id: int | None = None, camera_id: int | None = None) -> list[dict]:
        if bucket not in ("hour", "day"):
            raise Invalid("bucket must be 'hour' or 'day'")
        start = datetime.now(UTC) - timedelta(hours=max(1, hours))
        with self._uow() as uow:
            ids = set(visible_cameras(uow, viewer, cluster_id=cluster_id, camera_id=camera_id))
            events = uow.events.between(ids, start) if ids else []
        fmt = "%Y-%m-%d %H:00" if bucket == "hour" else "%Y-%m-%d"
        counts = Counter(e.created_at.strftime(fmt) for e in events)
        return [{"bucket": k, "violations": counts[k]} for k in sorted(counts)]

    def rank(self, viewer: Viewer, by: str = "camera", since_minutes: int = 60,
             cluster_id: int | None = None, limit: int = 5) -> list[dict]:
        if by not in RANK_BY:
            raise Invalid(f"by must be one of {list(RANK_BY)}")
        start = datetime.now(UTC) - timedelta(minutes=max(1, since_minutes))
        with self._uow() as uow:
            rows = visible_cameras(uow, viewer, cluster_id=cluster_id)
            events = uow.events.between(set(rows), start) if rows else []
        label = {"camera": lambda r: f"{r.id} - {r.name}", "node": lambda r: f"{r.node_id} - {r.node_name}",
                 "cluster": lambda r: f"{r.cluster_id} - {r.cluster_name}"}
        counts: Counter[str] = Counter(
            e.violation_type if by == "type" else label[by](rows[e.camera_id]) for e in events
        )
        return [{by: name, "violations": n} for name, n in counts.most_common(max(1, min(limit, 20)))]
