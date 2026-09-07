from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TypeVar

from app.domain.reconcile.models import Action, ActionType, Plan

K = TypeVar("K")
D = TypeVar("D")
O = TypeVar("O")


def reconcile(
    desired: Mapping[K, D],
    observed: Mapping[K, O],
    *,
    differs: Callable[[D, O], bool] = lambda desired_value, observed_value: desired_value != observed_value,
    delete_missing: bool = True,
) -> Plan[K, D, O]:
    actions: list[Action[K, D, O]] = []
    for key, want in desired.items():
        if key not in observed:
            actions.append(Action(ActionType.CREATE, key, desired=want, reason="absent"))
        elif differs(want, observed[key]):
            actions.append(Action(ActionType.UPDATE, key, desired=want, observed=observed[key], reason="drift"))
    if delete_missing:
        for key, have in observed.items():
            if key not in desired:
                actions.append(Action(ActionType.DELETE, key, observed=have, reason="unwanted"))
    return Plan(actions)


__all__ = ["reconcile"]