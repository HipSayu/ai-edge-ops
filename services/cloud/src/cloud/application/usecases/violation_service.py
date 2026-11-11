"""Reads violation events for one viewer, and the numbers over them (counts, trends, rankings, period comparisons).
The only place that decides which events a viewer may see."""

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from cloud.application.dto.scope import visible_cameras
from cloud.application.unit_of_work import UnitOfWorkFactory
from cloud.domain.violation.violations import EVENT_TYPES
from shared.errors import Invalid, NotAllowed
from shared.text import found
from shared.viewer import Viewer

_MAX_EVENTS = 50
RANK_BY = ("camera", "node", "cluster", "type")


@dataclass(frozen=True)
class EventView:
    event_id: int
    camera: str
    violation_type: str
    confidence: float
    at: str


@dataclass(frozen=True)
class ViolationSummary:
    since_minutes: int
    total: int
    by_type: dict[str, int]
    by_camera: dict[str, int]
    events: list[EventView] = field(default_factory=list)


class ViolationService:
    def __init__(self, uow: UnitOfWorkFactory) -> None:
        self._uow = uow

    def find(
        self,
        viewer: Viewer,
        since_minutes: int = 60,
        camera_id: int | None = None,
        cluster_id: int | None = None,
        violation_type: str | None = None,
        limit: int = 10,
    ) -> ViolationSummary:
        if violation_type and violation_type not in EVENT_TYPES:
            raise Invalid(f"violation_type phải là một trong {list(EVENT_TYPES)}")
        since = datetime.now(UTC) - timedelta(minutes=max(1, since_minutes))
        with self._uow() as uow:
            rows = visible_cameras(uow, viewer, cluster_id=cluster_id, camera_id=camera_id)
            if not rows:
                return ViolationSummary(since_minutes, 0, {}, {}, [])
            names = {cid: f"{cid} - {r.name} ({r.cluster_name} / {r.node_name})" for cid, r in rows.items()}
            ids = set(rows)
            by_type = uow.events.counts_by_type(ids, since, violation_type)
            by_camera = uow.events.counts_by_camera(ids, since, violation_type)
            events = uow.events.recent(ids, since, violation_type, min(limit, _MAX_EVENTS)) if limit > 0 else []
        return ViolationSummary(
            since_minutes,
            sum(by_type.values()),
            by_type,
            {names[cid]: n for cid, n in sorted(by_camera.items(), key=lambda kv: -kv[1])},
            [
                EventView(e.id, names[e.camera_id], e.violation_type, round(e.confidence, 2), e.created_at.isoformat())
                for e in events
            ],
        )

    def frame(self, viewer: Viewer, event_id: int) -> dict:
        with self._uow() as uow:
            event = found(uow.events.get(event_id), f"Không tìm thấy sự kiện {event_id}")
            if event.camera_id not in visible_cameras(uow, viewer):
                raise NotAllowed(f"Không tìm thấy sự kiện {event_id}")
        if not event.snapshot_path:
            raise NotAllowed(f"Sự kiện {event_id} không có ảnh")
        return {"event_id": event.id, "violation_type": event.violation_type, "at": event.created_at.isoformat()}

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

    def compare(self, viewer: Viewer, window_minutes: int = 60, cluster_id: int | None = None) -> dict:
        """The last window against the window right before it, in total and per violation type."""
        span = timedelta(minutes=max(1, window_minutes))
        now = datetime.now(UTC)
        with self._uow() as uow:
            ids = set(visible_cameras(uow, viewer, cluster_id=cluster_id))
            current = Counter(e.violation_type for e in uow.events.between(ids, now - span)) if ids else Counter()
            previous = (
                Counter(e.violation_type for e in uow.events.between(ids, now - 2 * span, now - span)) if ids else Counter()
            )
        types = sorted(set(current) | set(previous))
        return {
            "window_minutes": window_minutes,
            "current_total": sum(current.values()),
            "previous_total": sum(previous.values()),
            "by_type": {t: {"current": current[t], "previous": previous[t]} for t in types},
        }
