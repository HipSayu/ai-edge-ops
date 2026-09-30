from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from src.assistant.application.helpers.collections import ordered_union


class GraphState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    # Discoverable tools activated by search_tools / a matched skill; bound on later model calls.
    # They accumulate over the whole conversation, in first-activation order.
    active_tools: Annotated[list[str], ordered_union]
    # Model calls in the current turn; reset at the start of each turn
    rounds: int
