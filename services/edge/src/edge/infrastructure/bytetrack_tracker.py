import itertools
from types import SimpleNamespace

import numpy as np

from edge.domain.detection import Detection


class _Observed:
    """The detections of one call in the shape ByteTrack reads them: conf, xywh and cls, indexable by a boolean mask."""

    def __init__(self, conf: np.ndarray, xywh: np.ndarray, cls: np.ndarray) -> None:
        self.conf, self.xywh, self.cls = conf, xywh, cls

    def __len__(self) -> int:
        return len(self.conf)

    def __getitem__(self, mask) -> "_Observed":
        return _Observed(self.conf[mask], self.xywh[mask], self.cls[mask])


class ByteTrackTracker:
    """The Tracker port over Ultralytics' ByteTrack. One instance per camera: it remembers that camera's tracks, so a
    tracker shared between cameras would mix their ids. It follows each label separately, so a missing helmet and a
    missing vest on the same person do not compete for one track. It is called once per detection, not per camera frame."""

    def __init__(
        self, track_buffer: int = 30, high_thresh: float = 0.25, low_thresh: float = 0.1, new_track_thresh: float = 0.25,
        match_thresh: float = 0.8,
    ) -> None:
        self._args = SimpleNamespace(
            track_high_thresh=high_thresh, track_low_thresh=low_thresh, new_track_thresh=new_track_thresh,
            track_buffer=track_buffer, match_thresh=match_thresh, fuse_score=True,
        )
        self._trackers: dict[str, object] = {}
        self._ids = itertools.count(1)  # ours: ByteTrack's own counter is global, shared by cameras and reset by every new tracker

    def _tracker_of(self, label: str):
        if label not in self._trackers:
            from ultralytics.trackers.byte_tracker import BYTETracker  # heavy import, only when the runtime really starts

            self._trackers[label] = BYTETracker(self._args)
        return self._trackers[label]

    def update(self, detections: list[Detection]) -> list[Detection]:
        """The same detections, each with the id of its track; one the tracker has not confirmed yet keeps None."""
        ids: dict[int, int] = {}  # position in `detections` -> track id
        for label in {d.label for d in detections} | set(self._trackers):  # a label seen before is updated even when absent now
            members = [i for i, d in enumerate(detections) if d.label == label]
            boxes = np.array([detections[i].box for i in members], dtype=np.float32).reshape(-1, 4)
            observed = _Observed(
                np.array([detections[i].confidence for i in members], dtype=np.float32),
                np.stack([(boxes[:, 0] + boxes[:, 2]) / 2, (boxes[:, 1] + boxes[:, 3]) / 2,
                          boxes[:, 2] - boxes[:, 0], boxes[:, 3] - boxes[:, 1]], axis=1),
                np.zeros(len(members), dtype=np.float32),
            )
            tracker = self._tracker_of(label)
            tracker.update(observed)
            for track in tracker.tracked_stracks:  # the tracks that found a detection in this call
                if track.is_activated:
                    if not hasattr(track, "edge_id"):
                        track.edge_id = next(self._ids)
                    ids[members[int(track.idx)]] = track.edge_id  # a float in some ultralytics versions
        return [Detection(d.label, d.confidence, d.box, ids.get(i)) for i, d in enumerate(detections)]
