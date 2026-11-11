"""The dependency rule inside cloud, checked on the real imports: source code may only point inward.

    interface (cloud/interface)  ->  application  ->  domain  <-  infrastructure (implements the ports)

The routes, request schemas and the MCP server live in cloud/interface, so nothing here
imports them. The tools themselves (interface/mcp/tools.py) are plain functions here; the MCP server only publishes them.

Also: cloud never imports the assistant or the gateway, and shared imports no service."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # services/cloud
SRC = ROOT / "src" / "cloud"
SERVICES = ROOT.parent

FRAMEWORKS = ("sqlalchemy", "fastapi", "starlette", "cv2", "jwt", "pydantic", "cryptography", "httpx")


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


def layer_of(module: str) -> str | None:
    """'domain' | 'application' | 'infrastructure' | 'bootstrap' for a cloud module, else None."""
    parts = module.split(".")
    return parts[1] if parts[0] == "cloud" and len(parts) > 1 and parts[1] in (
        "domain", "application", "infrastructure", "bootstrap") else None


def test_domain_depends_on_nothing_inside_cloud_but_shared_kernel():
    bad = []
    for path in modules(SRC):
        if path.relative_to(SRC).parts[0] != "domain":
            continue
        for module in imports_of(path):
            if layer_of(module) in ("application", "infrastructure", "bootstrap"):
                bad.append(f"{path.name} imports {module}")
            if module.split(".")[0] in FRAMEWORKS:
                bad.append(f"{path.name} imports framework {module}")
    assert not bad, bad


def test_application_knows_no_infrastructure_or_frameworks():
    bad = []
    for path in modules(SRC):
        if path.relative_to(SRC).parts[0] != "application":
            continue
        for module in imports_of(path):
            if layer_of(module) in ("infrastructure", "bootstrap"):
                bad.append(f"{path.name} imports {module}")
            if module.split(".")[0] in FRAMEWORKS:
                bad.append(f"{path.name} imports framework {module}")
    assert not bad, bad


def test_nothing_imports_the_interface():
    bad = []
    for path in modules(SRC):
        for module in imports_of(path):
            if module.split(".")[0] == "apps":
                bad.append(f"{path.name} imports {module}")
    assert not bad, bad


def test_no_other_service_is_imported():
    bad = []
    for path in modules(SRC):
        for module in imports_of(path):
            if module.split(".")[0] in ("assistant", "gateway"):
                bad.append(f"{path.name} imports {module}")
    assert not bad, bad


def test_shared_imports_no_service():
    bad = []
    for path in modules(SERVICES / "shared" / "src" / "shared"):
        for module in imports_of(path):
            if module.split(".")[0] in ("cloud", "assistant", "gateway"):
                bad.append(f"{path.name} imports {module}")
    assert not bad, bad
