"""
Simple MCP Client

TODO:
- [x] Connect to server and list tools.
- [x] Create OpenAI/Ollama compatible tool formats
- [ ] Handle chatting with tool calling

"""

import asyncio
import logging
logger = logging.getLogger(__name__)
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel


class OpenAITool(BaseModel):
    """An OpenAI/Ollama formatted tool from an MCP server"""
    type: str = "function"
    function: dict


async def get_kubectl_tools(server_params: StdioServerParameters) -> list[object]:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            logger.info("Connected to MCP server with params {server_params}\n")

            try: 
                response = await session.list_tools()
                logger.info(f"Found {len(response.tools)} tools:\n")
                for tool in response.tools:
                    logger.info(f"  - {tool.name}")
                    logger.debug(f"    {tool.description}")
                    logger.debug(f"     Schema: {tool.inputSchema}")
                return response.tools
            except Exception as e:
                logger.error("Exception caught : {e}")
                return None


def format_tools(mcp_tools: list[dict]) -> list[dict]:
    formatted_tools = []
    for tool in mcp_tools:
        try:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema
                }
            })
            logger.info(f"Formatted: {tool.name} into OpenAI/Ollama compatible format")
        except Exception as e:
            logger.error(f"Exception formatting tool {tool.name}: {e}")
    logger.info(f"Formatted {len(formatted_tools)} tools.")
    return formatted_tools


async def main():
    logging.basicConfig(level=logging.INFO)

    server_params = StdioServerParameters(
        command="python",
        args=["kubectl_mcp.py"],
    )

    kubectl_tools = await get_kubectl_tools(server_params)
    fmt_kubectl_tools = format_tools(kubectl_tools)
    print(f"Formatted Tools:\n{list(t['function'].get('name') for t in fmt_kubectl_tools)}")

if __name__ == "__main__":
    asyncio.run(main())
