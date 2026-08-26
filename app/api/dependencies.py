from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.services.chat_service import ChatService


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    """Dependency injection helper for ChatService."""
    return ChatService(session=db)
