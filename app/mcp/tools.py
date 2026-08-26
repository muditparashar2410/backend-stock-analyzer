from typing import List, Dict, Any
from app.mcp.client import MCPClient


ALLOWED_SCHEMA_KEYS = {"type", "format", "description", "nullable", "enum", "properties", "required", "items"}


def sanitize_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively clean JSON schema for google-genai FunctionDeclaration compatibility.
    
    1. Retains only permitted OpenAPI schema keys (type, description, properties, required, items, enum, etc.).
    2. Converts type arrays like ['string', 'number'] to single string 'string'.
    """
    if not isinstance(schema, dict):
        return schema

    cleaned = {}
    for key, value in schema.items():
        if key not in ALLOWED_SCHEMA_KEYS:
            continue

        if key == "type" and isinstance(value, list):
            valid_types = [t for t in value if t != "null"]
            cleaned[key] = valid_types[0] if valid_types else "string"
        elif key == "properties" and isinstance(value, dict):
            cleaned[key] = {k: sanitize_schema(v) for k, v in value.items()}
        elif key == "items" and isinstance(value, dict):
            cleaned[key] = sanitize_schema(value)
        elif isinstance(value, dict):
            cleaned[key] = sanitize_schema(value)
        elif isinstance(value, list):
            cleaned[key] = [sanitize_schema(item) if isinstance(item, dict) else item for item in value]
        else:
            cleaned[key] = value

    return cleaned


async def get_formatted_tools(mcp_client: MCPClient) -> List[Dict[str, Any]]:
    """Fetch discovered tools from the MCP Client and format them for the LLMProvider."""
    raw_tools = await mcp_client.list_tools()
    formatted = []
    for tool in raw_tools:
        name = tool.get("name")
        description = tool.get("description", "")
        # Get input schema/parameters
        parameters = tool.get("inputSchema") or tool.get("parameters") or {
            "type": "object",
            "properties": {}
        }
        formatted.append({
            "name": name,
            "description": description,
            "parameters": sanitize_schema(parameters)
        })
    return formatted
