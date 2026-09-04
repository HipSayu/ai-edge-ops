from __future__ import annotations

from edge_agent.pipeline import evaluate_ppe
from edge_agent.runtime.base import Detection


def _d(label: str) -> Detection:
    return Detection(label=label, confidence=0.9, bbox=(0, 0, 1, 1))


def test_no_person_no_violation():
    assert evaluate_ppe([_d("helmet"), _d("vest")], ["helmet", "vest"]) == []


def test_missing_ppe_is_violation():
    assert evaluate_ppe([_d("person"), _d("vest")], ["helmet", "vest"]) == ["no_helmet"]


def test_explicit_negative_class_passthrough():
    out = evaluate_ppe([_d("person"), _d("no_helmet")], ["helmet"])
    assert "no_helmet" in out


def test_fully_compliant():
    assert evaluate_ppe([_d("person"), _d("helmet"), _d("vest")], ["helmet", "vest"]) == []
