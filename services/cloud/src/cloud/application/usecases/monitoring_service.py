"""The live wall: which cameras to show, the numbers over them, their streams and violation frames."""

import time
from datetime import UTC, datetime, timedelta

from cloud.application.ports import DetectionLookup, FeedControl, SnapshotStore, VideoStore
from cloud.application.dto.read_models import GridItem, LiveFrame, Overlay, OverlayBox, Stats
from cloud.application.dto.scope import visible_cameras
from cloud.application.unit_of_work import UnitOfWorkFactory
from cloud.domain.violation.priority import CameraLoad, GridRanker
from cloud.domain.violation.violation_event import ViolationEvent
from shared.errors import NotAllowed
from shared.text import found
from shared.viewer import Viewer

_GRID_WINDOW = timedelta(seconds=60)
_EVENTS_LIMIT = 200
_LIVE_MIN_DELAY_SEC = 0.1  # a frame is never shown sooner than this after it was made
_LIVE_MAX_DELAY_SEC = 0.5  # and, while its boxes have not come from the edge, waits this long for them at most
_DISPLAY_LAG_SEC = 0.7  # the frame on the viewer's screen is this much older than the newest the feed made (MJPEG buffering, measured by eye)


def blend(before: Overlay | None, after: Overlay | None, position: float) -> Overlay | None:
    """The boxes of a frame that lies between two detections. A box found in both (same label and track id) is moved
    in proportion to where the frame is between them; one found in only one belongs to the nearer detection."""
    if before is None or after is None or before is after:
        return before or after
    span = after.position_sec - before.position_sec
    f = (position - before.position_sec) / span if span > 0 else 1.0
    earlier = {(b.label, b.track_id): b for b in before.boxes if b.track_id is not None}
    boxes: list[OverlayBox] = []
    matched = set()
    for b in after.boxes:
        was = earlier.get((b.label, b.track_id)) if b.track_id is not None else None
        if was is not None:
            matched.add((b.label, b.track_id))
            moved = tuple(round(x0 + (x1 - x0) * f) for x0, x1 in zip(was.box, b.box))
            boxes.append(OverlayBox(b.label, b.confidence, moved, b.track_id))
        elif f >= 0.5:
            boxes.append(b)
    if f < 0.5:
        boxes.extend(b for b in before.boxes if b.track_id is None or (b.label, b.track_id) not in matched)
    return Overlay(after.camera_id, position, after.width, after.height, tuple(boxes))


class MonitoringService:
    def __init__(
        self, uow: UnitOfWorkFactory, feeds: FeedControl, videos: VideoStore, snapshots: SnapshotStore, grid_size: int,
        detections: DetectionLookup,
    ) -> None:
        self._uow, self._feeds, self._videos, self._snapshots, self._grid_size = uow, feeds, videos, snapshots, grid_size
        self._detections = detections
        # One ranker per visible set: a user who sees other cameras gets their own stable grid
        self._rankers: dict[frozenset[int], GridRanker] = {}

    def grid(self, viewer: Viewer, cluster_id: int | None = None) -> list[GridItem]:
        """Cameras the wall shows, already ordered. Cameras with violations or people come first."""
        if cluster_id is not None:
            viewer.require_cluster(cluster_id)
        since = datetime.now(UTC) - _GRID_WINDOW
        with self._uow() as uow:
            rows = {cid: r for cid, r in visible_cameras(uow, viewer, cluster_id=cluster_id).items() if r.enabled}
            recent = uow.events.counts_by_camera(set(rows), since) if rows else {}

        people = {cid: self._feeds.person_count(cid) for cid in rows}
        loads = [CameraLoad(cid, people[cid], recent.get(cid, 0)) for cid in rows]
        ranker = self._rankers.setdefault(frozenset(rows), GridRanker(self._grid_size))
        order = ranker.rank(loads, time.monotonic())
        return [
            GridItem(rows[cid], people[cid], recent.get(cid, 0), round(ranker.score(cid), 1), self._detections.online(cid))
            for cid in order
        ]

    def stats(self, viewer: Viewer, cluster_id: int | None = None, since_minutes: int = 60) -> Stats:
        if cluster_id is not None:
            viewer.require_cluster(cluster_id)
        since = datetime.now(UTC) - timedelta(minutes=since_minutes)
        with self._uow() as uow:
            ids = set(visible_cameras(uow, viewer, cluster_id=cluster_id))
            by_type = uow.events.counts_by_type(ids, since) if ids else {}
        return Stats(total=sum(by_type.values()), by_type=by_type)

    def camera_events(self, viewer: Viewer, camera_id: int, limit: int = 30) -> list[ViolationEvent]:
        with self._uow() as uow:
            visible_cameras(uow, viewer, camera_id=camera_id)
            return uow.events.recent({camera_id}, limit=min(limit, _EVENTS_LIMIT))

    def open_stream(self, viewer: Viewer, camera_id: int) -> None:
        """Checks the viewer may watch the camera and makes sure its feed is running."""
        with self._uow() as uow:
            row = visible_cameras(uow, viewer).get(camera_id)
        if row is None or not row.enabled:
            raise NotAllowed("Không tìm thấy camera")
        self._feeds.ensure(camera_id, self._videos.folder(row.cluster_id, row.node_id, row.id))

    def require_streams(self, viewer: Viewer, camera_ids: list[int]) -> None:
        """The viewer may watch every one of these cameras; makes sure their feeds run."""
        for camera_id in camera_ids:
            self.open_stream(viewer, camera_id)

    def overlay(self, camera_id: int) -> Overlay | None:
        """The boxes that belong to the frame the viewer is looking at now. In memory only: no permission check here,
        callers have made it with require_streams."""
        position = self._feeds.position(camera_id)
        if position is None:
            return None
        return self._detections.at(camera_id, max(0.0, position - _DISPLAY_LAG_SEC))

    def live_frame(self, camera_id: int, after_seq: int) -> LiveFrame | None:
        """The next frame of the camera with the boxes found on it. It is shown at once when its boxes are known, and waits a
        moment for them when they are not.
        None when there is nothing yet; the caller asks again a moment later."""
        entry = self._feeds.frame_after(camera_id, after_seq)
        if entry is None or entry[1] < _LIVE_MIN_DELAY_SEC:
            return None
        seq, age, position, jpeg = entry
        overlay = None
        if position is not None:
            before, after = self._detections.around(camera_id, position)
            if after is None and age < _LIVE_MAX_DELAY_SEC:
                return None  # the detection after this frame may still be on the way: wait for it, but not for ever
            overlay = blend(before, after, position)
        return LiveFrame(seq, jpeg, overlay, self._detections.speed(camera_id), age)

    def latest_frame(self, camera_id: int) -> bytes:
        return self._feeds.latest_frame(camera_id)

    def snapshot(self, viewer: Viewer, event_id: int) -> bytes:
        """The frame saved with a violation. Same visibility rule as the camera it came from."""
        with self._uow() as uow:
            event = found(uow.events.get(event_id), "Không tìm thấy ảnh")
            visible = visible_cameras(uow, viewer)
        if event.camera_id not in visible or not event.snapshot_path:
            raise NotAllowed("Không tìm thấy ảnh")
        return found(self._snapshots.read(event.snapshot_path), "Không tìm thấy ảnh")
