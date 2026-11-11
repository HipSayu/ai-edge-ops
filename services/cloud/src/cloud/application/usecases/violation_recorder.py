"""Records a violation an edge runtime reported: saves the frame, then the event."""

from collections.abc import Callable

from cloud.application.ports import SnapshotStore
from cloud.application.unit_of_work import UnitOfWorkFactory
from cloud.domain.violation.violation_event import ViolationEvent

# on_event(camera_id, violation_type, confidence, video_ts_sec, jpeg_bytes)
EventSink = Callable[[int, str, float, float, bytes], None]


class ViolationRecorder:
    def __init__(self, uow: UnitOfWorkFactory, snapshots: SnapshotStore) -> None:
        self._uow, self._snapshots = uow, snapshots

    def record(self, camera_id: int, violation_type: str, confidence: float, video_ts_sec: float, jpeg: bytes) -> None:
        name = self._snapshots.save(jpeg)
        event = ViolationEvent(
            camera_id=camera_id, violation_type=violation_type, confidence=confidence,
            video_ts_sec=video_ts_sec, snapshot_path=name,
        )
        with self._uow() as uow:
            uow.events.add(event)
