from dataclasses import dataclass, field
from datetime import UTC, datetime

from cloud.domain.violation.violations import EVENT_TYPES
from shared.errors import Invalid


@dataclass
class ViolationEvent:
    """One recorded violation: what the detector saw on a camera, and the frame saved with it."""

    camera_id: int
    violation_type: str
    confidence: float
    video_ts_sec: float = 0.0
    snapshot_path: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: int | None = None

    def __post_init__(self) -> None:
        if self.violation_type not in EVENT_TYPES:
            raise Invalid(f"Loại vi phạm phải là một trong {list(EVENT_TYPES)}")
