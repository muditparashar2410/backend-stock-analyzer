from fastapi import APIRouter, Depends, HTTPException, status
from app.agent.schemas import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.api.dependencies import get_chat_service
from app.utils.logging import logger

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service)
):
    """Process a user question regarding Indian stocks, using LLM & Tapetide MCP tools."""
    try:
        response = await service.process_chat(
            user_message=request.message,
            conversation_id=request.conversation_id
        )
        return response
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
