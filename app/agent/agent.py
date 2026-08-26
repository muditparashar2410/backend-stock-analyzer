import json
from typing import List, Optional
from app.llm.base import LLMProvider, LLMMessage
from app.mcp.client import MCPClient
from app.mcp.tools import get_formatted_tools
from app.agent.prompts import SYSTEM_PROMPT, TITLE_GENERATION_PROMPT
from app.utils.logging import logger


class StockAgent:
    """Provider-Independent Stock Research AI Agent.
    
    Coordinates conversation history, LLM decision making, MCP tool execution,
    and final financial analysis response generation.
    """

    def __init__(self, llm_provider: LLMProvider, mcp_client: MCPClient):
        self.llm = llm_provider
        self.mcp = mcp_client

    async def run(
        self,
        user_message: str,
        history: Optional[List[LLMMessage]] = None,
        max_tool_iterations: int = 3
    ) -> str:
        messages = list(history or [])
        messages.append(LLMMessage(role="user", content=user_message))

        # Discover MCP tools
        tools = await get_formatted_tools(self.mcp)

        iteration = 0
        while iteration < max_tool_iterations:
            iteration += 1
            logger.info(f"Agent iteration {iteration}/{max_tool_iterations}...")
            
            response = await self.llm.generate(
                messages=messages,
                system_instruction=SYSTEM_PROMPT,
                tools=tools
            )

            # If LLM requested tool calls, execute them
            if response.tool_calls:
                logger.info(f"LLM requested {len(response.tool_calls)} tool call(s).")
                tool_results_summary = []

                for tool_call in response.tool_calls:
                    logger.info(f"Executing tool '{tool_call.name}' with args {tool_call.arguments}")
                    result = await self.mcp.call_tool(tool_call.name, tool_call.arguments)
                    tool_results_summary.append({
                        "tool": tool_call.name,
                        "args": tool_call.arguments,
                        "result": result
                    })

                # Append tool call outputs back to message history as a user data observation turn
                messages.append(
                    LLMMessage(
                        role="user",
                        content=f"[Retrieved Market Data from MCP Tools]: {json.dumps(tool_results_summary, indent=2)}\n\nPlease synthesize the above retrieved data into a structured financial analysis for the user."
                    )
                )
            else:
                # LLM produced final response
                if response.content:
                    return response.content
                break

        # Fallback if loop ended after max iterations
        final_resp = await self.llm.generate(
            messages=messages,
            system_instruction=SYSTEM_PROMPT
        )
        return final_resp.content or "I have processed your query based on the retrieved market data."

    async def generate_title(self, first_message: str) -> str:
        """Generate a short title for a new conversation based on the first query."""
        try:
            prompt = TITLE_GENERATION_PROMPT.format(first_message=first_message)
            resp = await self.llm.generate(
                messages=[LLMMessage(role="user", content=prompt)]
            )
            title = (resp.content or "").strip().strip('"').strip("'")
            return title if title and len(title) < 50 else first_message[:30]
        except Exception as e:
            logger.warning(f"Failed to generate title via LLM: {e}")
            return first_message[:30]
