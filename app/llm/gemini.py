import json
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

from app.llm.base import LLMProvider, LLMMessage, LLMResponse, ToolCall
from app.config.settings import settings
from app.utils.logging import logger


class GeminiProvider(LLMProvider):
    """Gemini LLM Provider using Google's official 'google-genai' SDK."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model or settings.GEMINI_MODEL

        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. GeminiProvider will fail if invoked without key.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

    async def generate(
        self,
        messages: List[LLMMessage],
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        if not self.client:
            raise ValueError("GEMINI_API_KEY is required to initialize Gemini client.")

        # Convert messages to Gemini format and merge consecutive turns of the same role
        contents = []
        for msg in messages:
            role = "user" if msg.role == "user" else "model"
            if msg.role == "system":
                # System prompt is passed via config in google-genai
                continue
            if contents and contents[-1].role == role:
                # Merge consecutive turns of the same role to satisfy Gemini API constraints
                contents[-1].parts.append(types.Part.from_text(text=f"\n{msg.content}"))
            else:
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg.content)]
                    )
                )

        # Gemini API requires that requests MUST NOT end on a 'model' turn
        if contents and contents[-1].role == "model":
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="Please synthesize the response based on the above information.")]
                )
            )

        config_kwargs = {}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        # Map tools if provided
        if tools:
            # Convert JSON schema tool definitions to Gemini FunctionDeclarations
            function_declarations = []
            for tool_def in tools:
                func_decl = types.FunctionDeclaration(
                    name=tool_def.get("name"),
                    description=tool_def.get("description", ""),
                    parameters=tool_def.get("parameters") or tool_def.get("inputSchema")
                )
                function_declarations.append(func_decl)
            
            if function_declarations:
                config_kwargs["tools"] = [types.Tool(function_declarations=function_declarations)]

        config = types.GenerateContentConfig(**config_kwargs)

        try:
            logger.info(f"Calling Gemini API ({self.model_name}) with {len(contents)} message history items...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            tool_calls: List[ToolCall] = []
            text_response: Optional[str] = None

            if response.function_calls:
                for idx, call in enumerate(response.function_calls):
                    tool_calls.append(
                        ToolCall(
                            id=f"call_{idx}_{call.name}",
                            name=call.name,
                            arguments=call.args if isinstance(call.args, dict) else dict(call.args or {})
                        )
                    )
            
            if response.text:
                text_response = response.text

            return LLMResponse(
                content=text_response,
                tool_calls=tool_calls,
                finish_reason="tool_calls" if tool_calls else "stop"
            )

        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            raise RuntimeError(f"Gemini LLM Provider failed: {str(e)}")
