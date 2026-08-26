from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.database.models import Conversation, Message


class ConversationRepository:
    """Repository handling all database persistence operations for chat conversations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_conversation(self, title: str = "New Stock Chat") -> Conversation:
        conversation = Conversation(title=title)
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_conversations(self) -> List[Conversation]:
        stmt = (
            select(Conversation)
            .order_by(Conversation.updated_at.desc())
            .options(selectinload(Conversation.messages))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_title(self, conversation_id: str, new_title: str) -> Optional[Conversation]:
        conversation = await self.get_conversation(conversation_id)
        if conversation:
            conversation.title = new_title
            conversation.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(conversation)
        return conversation

    async def delete_conversation(self, conversation_id: str) -> bool:
        stmt = delete(Conversation).where(Conversation.id == conversation_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def add_message(self, conversation_id: str, role: str, content: str) -> Message:
        message = Message(conversation_id=conversation_id, role=role, content=content)
        self.session.add(message)

        # Update parent conversation timestamp
        conversation = await self.get_conversation(conversation_id)
        if conversation:
            conversation.updated_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_messages(self, conversation_id: str) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
