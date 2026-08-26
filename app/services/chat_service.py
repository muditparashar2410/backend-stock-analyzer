from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import ConversationRepository
from app.llm.factory import get_llm_provider
from app.llm.base import LLMMessage
from app.mcp.client import MCPClient
from app.agent.agent import StockAgent
from app.agent.schemas import ChatResponse, ConversationDTO, MessageDTO
from app.utils.logging import logger


class ChatService:
    """Business service coordinating database history and AI Agent execution."""

    def __init__(self, session: AsyncSession):
        self.repo = ConversationRepository(session)
        self.llm = get_llm_provider()
        self.mcp = MCPClient()
        self.agent = StockAgent(self.llm, self.mcp)

    async def process_chat(self, user_message: str, conversation_id: Optional[str] = None) -> ChatResponse:
        # 1. Retrieve or create conversation
        if conversation_id:
            conversation = await self.repo.get_conversation(conversation_id)
            if not conversation:
                logger.info(f"Conversation {conversation_id} not found. Creating new conversation.")
                conversation = await self.repo.create_conversation()
        else:
            conversation = await self.repo.create_conversation()

        conversation_id = conversation.id

        # 2. Fetch existing history
        messages_db = await self.repo.get_messages(conversation_id)
        history = [
            LLMMessage(role=m.role, content=m.content)
            for m in messages_db
        ]

        # 3. Store user message in DB
        user_msg_db = await self.repo.add_message(conversation_id, "user", user_message)

        # 4. Generate title if first message
        new_title: Optional[str] = None
        if len(messages_db) == 0:
            new_title = await self.agent.generate_title(user_message)
            await self.repo.update_title(conversation_id, new_title)

        # 5. Run AI Agent
        assistant_content = await self.agent.run(user_message=user_message, history=history)

        # 6. Store assistant response in DB
        assistant_msg_db = await self.repo.add_message(conversation_id, "assistant", assistant_content)

        return ChatResponse(
            conversation_id=conversation_id,
            message_id=assistant_msg_db.id,
            role="assistant",
            content=assistant_content,
            title=new_title or conversation.title
        )

    async def list_conversations(self) -> List[ConversationDTO]:
        convs = await self.repo.list_conversations()
        result = []
        for c in convs:
            msgs = [
                MessageDTO(
                    id=m.id,
                    conversation_id=m.conversation_id,
                    role=m.role,
                    content=m.content,
                    created_at=m.created_at
                )
                for m in c.messages
            ]
            result.append(
                ConversationDTO(
                    id=c.id,
                    title=c.title,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    messages=msgs
                )
            )
        return result

    async def get_conversation(self, conversation_id: str) -> Optional[ConversationDTO]:
        c = await self.repo.get_conversation(conversation_id)
        if not c:
            return None
        msgs = [
            MessageDTO(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                created_at=m.created_at
            )
            for m in c.messages
        ]
        return ConversationDTO(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            messages=msgs
        )

    async def create_conversation(self, title: str = "New Stock Chat") -> ConversationDTO:
        c = await self.repo.create_conversation(title=title)
        return ConversationDTO(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            messages=[]
        )

    async def delete_conversation(self, conversation_id: str) -> bool:
        return await self.repo.delete_conversation(conversation_id)
