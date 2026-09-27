"""Slash commands for the assistant chat.

* ``direct``  — handled here, no LLM: instant, deterministic, free.
* ``prompt``  — a macro that expands to a prompt and runs through the agent.

    /help                list commands
    /clear               clear the conversation
    /health              fleet health snapshot (direct)
    /violations [hours]  PPE violation summary (prompt)
    /alerts              open alerts, most severe first (prompt)
    /deployments         active + failed deployments (prompt)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.mcp.tools import fleet, observability


@dataclass(frozen=True)
class SlashCommand:
    name: str
    desc: str
    kind: str  # "direct" | "prompt" | "control"
    prompt: str | None = None
    handler: Callable[[str], Awaitable[str]] | None = None


async def _help(_: str) -> str:
    lines = [f"/{c.name} — {c.desc}" for c in COMMANDS.values()]
    return "Commands:\n" + "\n".join(lines)


async def _health(_: str) -> str:
    h = await fleet.fleet_health()
    return (
        f"Fleet: {h['online']}/{h['total']} online, {h['degraded']} degraded, "
        f"{h['offline']} offline, {h['provisioning']} provisioning. "
        f"avg latency 24h: {h['avg_inference_latency_ms_24h']} ms."
    )


async def _violations_now(arg: str) -> str:
    hours = int(arg) if arg.strip().isdigit() else 24
    by_type = await observability.violations_by_type(days=max(1, hours // 24 or 1))
    recent = await observability.list_violations(hours=hours, limit=10)
    parts = [f"{r['label']}={r['count']}" for r in by_type["by_type"]]
    return f"Last {hours}h: {recent['total']} violations ({', '.join(parts) or 'none'})."


COMMANDS: dict[str, SlashCommand] = {
    "help": SlashCommand("help", "list commands", "direct", handler=_help),
    "clear": SlashCommand("clear", "clear the conversation", "control"),
    "health": SlashCommand("health", "fleet health snapshot", "direct", handler=_health),
    "violations": SlashCommand(
        "violations", "PPE violation summary", "direct", handler=_violations_now
    ),
    "alerts": SlashCommand(
        "alerts", "open alerts, most severe first", "prompt",
        prompt="List all open alerts, ordered most severe first, with device ids.",
    ),
    "deployments": SlashCommand(
        "deployments", "active + failed deployments", "prompt",
        prompt="Show active deployments and any that failed recently.",
    ),
    "overview": SlashCommand(
        "overview", "top-line KPIs", "prompt",
        prompt="Give me the analytics overview and call out anything unusual.",
    ),
}


def parse(text: str) -> tuple[SlashCommand | None, str]:
    """('/health 24') -> (SlashCommand, '24'). Non-slash -> (None, text)."""
    if not text.startswith("/"):
        return None, text
    name, _, arg = text[1:].strip().partition(" ")
    return COMMANDS.get(name.lower()), arg.strip()


__all__ = ["COMMANDS", "SlashCommand", "parse"]
