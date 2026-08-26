from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    """Abstract message structure for LLM providers."""
    role: str  # 'user', 'assistant', 'system'
    content: str


class ToolCall(BaseModel):
    """Abstract structure representing an LLM request to invoke an external tool."""
    id: str = Field(default="")
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Abstract response from an LLM provider."""
    content: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    finish_reason: str = "stop"


class LLMProvider(ABC):
    """Abstract Interface for LLM Providers.
    
    This abstracts away specific SDKs (Gemini, OpenAI, Anthropic) from the Agent logic.
    """

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        """Generate a response from the LLM given messages and available tool definitions."""
        pass
