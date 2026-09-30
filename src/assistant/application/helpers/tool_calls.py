import json
from collections.abc import Sequence

from langchain_core.messages import AIMessage


def drop_empty_args(tool_calls: Sequence[dict]) -> list[dict]:
    """Drop None/"" args: models often fill optional args with "" instead of omitting them."""
    return [
        {**call, "args": {k: v for k, v in (call.get("args") or {}).items() if v not in (None, "")}}
        for call in tool_calls
    ]


def call_signature(call: dict) -> str:
    """Identity of a call by name + args, to run duplicates in one batch once."""
    return f"{call['name']}:{json.dumps(call['args'], sort_keys=True, default=str)}"


def has_tool_calls(state: dict) -> bool:
    last = state["messages"][-1]
    return isinstance(last, AIMessage) and bool(last.tool_calls)
