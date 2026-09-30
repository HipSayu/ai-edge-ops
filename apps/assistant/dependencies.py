"""Service accessors for the Assistant routers; `create_app` stores the container on `app.state`."""

from fastapi import Request

from src.assistant.bootstrap.assistant_container import AssistantContainer
from src.assistant.application.services.chat_stream_service import ChatStreamService


def get_container(request: Request) -> AssistantContainer:
    return request.app.state.container


def get_chat_stream_service(request: Request) -> ChatStreamService:
    return get_container(request).chat_stream_service
