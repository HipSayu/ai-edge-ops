from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar

K = TypeVar("K")
D = TypeVar("D")
O = TypeVar("O")


class ActionType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Action(Generic[K, D, O]):
    type: ActionType
    key: K
    desired: D | None = None
    observed: O | None = None
    reason: str = ""


@dataclass(frozen=True)
class Plan(Generic[K, D, O]):
    actions: list[Action[K, D, O]] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.actions)

    def of(self, action_type: ActionType) -> list[Action[K, D, O]]:
        return [action for action in self.actions if action.type is action_type]

    @property
    def creates(self) -> list[Action[K, D, O]]:
        return self.of(ActionType.CREATE)

    @property
    def updates(self) -> list[Action[K, D, O]]:
        return self.of(ActionType.UPDATE)

    @property
    def deletes(self) -> list[Action[K, D, O]]:
        return self.of(ActionType.DELETE)


__all__ = ["ActionType", "Action", "Plan"]