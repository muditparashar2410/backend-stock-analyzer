import httpx
from typing import List, Dict, Any, Optional
from app.config.settings import settings
from app.utils.logging import logger


class MCPClient:
    """Provider-independent MCP Client for connecting to remote Streamable HTTP/SSE MCP Servers (e.g. Tapetide)."""

    def __init__(self, server_url: Optional[str] = None, api_key: Optional[str] = None):
        self.server_url = server_url or settings.MCP_SERVER_URL
        self.api_key = api_key or settings.TAPETIDE_API_KEY
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
            self.headers["x-api-key"] = self.api_key

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Dynamically discover available tools from the remote MCP server."""
        logger.info(f"Connecting to MCP server at {self.server_url} to discover tools...")
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(self.server_url, json=payload, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("result", {})
                    tools = result.get("tools", [])
                    logger.info(f"Discovered {len(tools)} tools from MCP server.")
                    return tools
                else:
                    logger.warning(f"MCP tools/list returned HTTP {response.status_code}. Returning fallback default tools.")
                    return self._fallback_tools()
            except Exception as e:
                logger.error(f"Failed to connect to MCP server at {self.server_url}: {str(e)}. Using fallback tools schema.")
                return self._fallback_tools()

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a discovered tool on the remote MCP server."""
        logger.info(f"Executing MCP tool '{tool_name}' with args: {arguments}")
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        async with httpx.AsyncClient(timeout=25.0) as client:
            try:
                response = await client.post(self.server_url, json=payload, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("result", {})
                    return result
                else:
                    logger.error(f"MCP tool call '{tool_name}' failed with HTTP {response.status_code}: {response.text}")
                    return {"error": f"Tool execution failed with status {response.status_code}"}
            except Exception as e:
                logger.error(f"Error calling MCP tool '{tool_name}': {str(e)}")
                return {"error": f"Failed to execute tool '{tool_name}': {str(e)}"}

    def _fallback_tools(self) -> List[Dict[str, Any]]:
        """Fallback tool declarations matching standard Indian stock market endpoints when offline."""
        return [
            {
                "name": "get_stock_quote",
                "description": "Fetch real-time stock price and quote details for an Indian stock (NSE/BSE).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock symbol or company name e.g. RELIANCE, TCS, INFY, HDFCBANK"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_company_financials",
                "description": "Fetch financial overview, valuation metrics, P/E ratio, market cap, and revenue for an Indian company.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock symbol e.g. RELIANCE, TCS"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_ipo_details",
                "description": "Fetch IPO issue details, listing date, issue price, and listing gain for Indian IPOs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol_or_name": {"type": "string", "description": "Company or IPO name e.g. Tata Technologies, Swiggy, Hyundai"}
                    },
                    "required": ["symbol_or_name"]
                }
            },
            {
                "name": "get_stock_news",
                "description": "Fetch recent news and corporate action updates for Indian equities.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock symbol or company name"}
                    },
                    "required": ["symbol"]
                }
            }
        ]
