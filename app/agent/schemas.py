from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = Field(None, description="UUID of existing conversation, or null for new chat")
    message: str = Field(..., min_length=1, description="User question or query about Indian stocks")


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    role: str = "assistant"
    content: str
    title: Optional[str] = None


class MessageDTO(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime


class ConversationDTO(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageDTO] = Field(default_factory=list)
