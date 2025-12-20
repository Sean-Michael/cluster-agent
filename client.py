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
from mcp.types import Tool as MCPTool
from mcp.client.stdio import stdio_client
from pydantic import BaseModel
import ollama


class OpenAITool(BaseModel):
    """An OpenAI/Ollama formatted tool Object"""
    type: str = "function"
    function: dict


async def get_kubectl_tools(server_params: StdioServerParameters) -> list[MCPTool] | None:
    """Uses MCPClient to list_tools(), returns a list MCPTool objects."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            logger.info(f"Connected to MCP server with params {server_params}\n")

            try: 
                response = await session.list_tools()
                logger.info(f"Found {len(response.tools)} tools:\n")
                for tool in response.tools:
                    logger.info(f"  - {tool.name}")
                    logger.debug(f"    {tool.description}")
                    logger.debug(f"     Schema: {tool.inputSchema}")
                return response.tools
            except Exception as e:
                logger.error(f"Exception caught : {e}")
                return None


def format_tools(mcp_tools: list[MCPTool]) -> list[OpenAITool]:
    """Converts an MCPTool into an OpenAITool, returns list of OpenAITool objects."""
    formatted_tools = []
    for tool in mcp_tools:
        try:
            formatted_tools.append(OpenAITool(
                function = {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema
                }
            ))
            logger.info(f"Formatted: {tool.name} into OpenAI/Ollama compatible format")
        except Exception as e:
            logger.error(f"Exception formatting tool {tool.name}: {e}")
    logger.info(f"Formatted {len(formatted_tools)} tools.")
    return formatted_tools


def chat_with_tool(model: str, messages: dict[str], tools: list[OpenAITool]) -> dict | None:
    try:
        response = ollama.chat(
            model=model,
            messages=messages,
            tools = tools
        )
        return response
    except Exception as e:
        logger.error(f"Exception in Ollama chat: {e}")
        return None


async def main():
    logging.basicConfig(level=logging.INFO)

    server_params = StdioServerParameters(
        command="python",
        args=["kubectl_mcp.py"],
    )

    kubectl_tools = await get_kubectl_tools(server_params)
    kubectl_tools_dict = [t.model_dump() for t in format_tools(kubectl_tools)]

    messages = [{"role": "user", "content": "Show me what nodes are in my kubernetes cluster"}]
    test_response = chat_with_tool("mistral-nemo:latest", messages, kubectl_tools_dict)
    print(test_response)

if __name__ == "__main__":
    asyncio.run(main())
