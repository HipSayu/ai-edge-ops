from fastapi import APIRouter, Depends, status

from apps.cloud.api.v1.conversation_schemas import (
    ChatMessageCreate, ChatMessageOut, ConversationCreate, ConversationOut, ConversationUpdate,
)
from apps.cloud.dependencies import get_conversation_service, require_principal
from src.cloud.application.services.conversation_service import ConversationService
from src.cloud.domain.entities.chat_message import ChatRole
from src.cloud.domain.value_objects.principal import Principal
from src.shared.exceptions import AppException, ErrorCode

# The signed-in user's assistant conversations. The dashboard chats with the assistant using the conversation
# id as session_id, and records the messages shown here; the assistant itself only keeps the agent's memory.
router = APIRouter(prefix="/conversations", tags=["conversations"])


async def current_user(principal: Principal = Depends(require_principal)) -> str:
    if not principal.is_user:
        raise AppException(ErrorCode.FORBIDDEN, "Conversations belong to user accounts, not service API keys")
    return principal.subject


@router.get("", response_model=list[ConversationOut])
async def list_conversations(
    user_id: str = Depends(current_user), service: ConversationService = Depends(get_conversation_service)
):
    """Most recently active first."""
    return await service.list(user_id)


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate,
    user_id: str = Depends(current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    return await service.create(user_id, body.title)


@router.patch("/{conversation_id}", response_model=ConversationOut)
async def rename_conversation(
    conversation_id: str,
    body: ConversationUpdate,
    user_id: str = Depends(current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    return await service.rename(user_id, conversation_id, body.title)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    user_id: str = Depends(current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    await service.delete(user_id, conversation_id)


@router.get("/{conversation_id}/messages", response_model=list[ChatMessageOut])
async def list_messages(
    conversation_id: str,
    user_id: str = Depends(current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    """Oldest first."""
    return await service.messages(user_id, conversation_id)


@router.post("/{conversation_id}/messages", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
async def add_message(
    conversation_id: str,
    body: ChatMessageCreate,
    user_id: str = Depends(current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    """An untitled conversation takes its first question as title."""
    return await service.add_message(user_id, conversation_id, ChatRole(body.role), body.content, body.metadata)
