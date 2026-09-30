from dataclasses import dataclass

from src.cloud.domain.value_objects.model_ref import ModelRef


@dataclass(frozen=True, slots=True)
class ModelLocation:
    """A resolved, pinned model file that edge nodes can download."""

    ref: ModelRef
    url: str
    commit_sha: str
