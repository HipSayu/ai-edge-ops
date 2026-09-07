from __future__ import annotations

from app.domain.reconcile import ActionType, reconcile


def test_create_update_delete():
    desired = {"a": 1, "b": 2, "c": 3}
    observed = {"b": 2, "c": 99, "d": 4}
    plan = reconcile(desired, observed)
    assert {a.key for a in plan.creates} == {"a"}
    assert {a.key for a in plan.updates} == {"c"}
    assert {a.key for a in plan.deletes} == {"d"}
    assert bool(plan) is True


def test_no_drift_empty_plan():
    plan = reconcile({"a": 1}, {"a": 1})
    assert not plan
    assert plan.actions == []


def test_delete_missing_disabled():
    plan = reconcile({"a": 1}, {"a": 1, "b": 2}, delete_missing=False)
    assert plan.deletes == []


def test_custom_differ():
    desired = {"x": {"version": 2, "note": "new"}}
    observed = {"x": {"version": 2, "note": "old"}}
    plan = reconcile(desired, observed, differs=lambda d, o: d["version"] != o["version"])
    assert not plan
    assert plan.of(ActionType.UPDATE) == []