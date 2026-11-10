"""The dependency rule inside the edge runtime, checked on the real imports: source code may only point inward.

    bootstrap  ->  application  ->  domain  <-  infrastructure (implements the ports)

It never imports another service's code: the cloud is reached over MQTT only, and the topics, messages and the
sending side come from the shared `edge_link` package."""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "edge"
OTHER_SERVICES = ("cloud", "assistant", "gateway", "shared")  # edge_link is the one thing it shares with the cloud


def imports_of(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def modules(folder: Path) -> list[Path]:
    return [p for p in folder.rglob("*.py") if "__pycache__" not in p.parts]


def test_domain_is_pure():
    bad = [f"{p.name} imports {m}" for p in modules(SRC / "domain") for m in imports_of(p)
           if m.split(".")[0] in ("cv2", "paho", "ultralytics", "pydantic", "numpy")
           or m.startswith("edge.") and not m.startswith("edge.domain")]
    assert not bad, bad


def test_application_knows_no_infrastructure_or_protocols():
    bad = [f"{p.name} imports {m}" for p in modules(SRC / "application") for m in imports_of(p)
           if m.split(".")[0] in ("cv2", "paho", "ultralytics", "pydantic")
           or m.startswith("edge.infrastructure") or m.startswith("edge.bootstrap")]
    assert not bad, bad


def test_never_imports_another_service():
    bad = [f"{p} imports {m}" for p in modules(SRC) for m in imports_of(p) if m.split(".")[0] in OTHER_SERVICES]
    assert not bad, bad
