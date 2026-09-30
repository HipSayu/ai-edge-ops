from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelRef:
    """Points at one model file in a model store; `revision` may be a branch, tag or commit sha."""

    repo_id: str
    filename: str
    revision: str = "main"
