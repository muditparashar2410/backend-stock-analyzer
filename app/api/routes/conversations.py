from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.agent.schemas import ConversationDTO
from app.services.chat_service import ChatService
from app.api.dependencies import get_chat_service
from app.utils.logging import logger

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.get("", response_model=List[ConversationDTO])
async def list_conversations(service: ChatService = Depends(get_chat_service)):
    """Retrieve all conversations ordered by recent activity."""
    return await service.list_conversations()


@router.post("", response_model=ConversationDTO, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    title: str = "New Stock Chat",
    service: ChatService = Depends(get_chat_service)
):
    """Create a new empty chat conversation."""
    return await service.create_conversation(title=title)


@router.get("/{conversation_id}", response_model=ConversationDTO)
async def get_conversation(
    conversation_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """Retrieve a specific conversation along with all its messages."""
    conversation = await service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found."
        )
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """Delete a conversation and all associated messages."""
    deleted = await service.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found."
        )
    return None
