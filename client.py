"""
Simple MCP Client

TODO:
- [x] Connect to server and list tools.
- [x] Create OpenAI/Ollama compatible tool formats
- [x] Handle chatting with tool calling
- [ ] Handle tool execution and callback

"""

import asyncio
import logging
logger = logging.getLogger(__name__)
from mcp import ClientSession, StdioServerParameters
from mcp.types import Tool as MCPTool
from mcp.client.stdio import stdio_client
from pydantic import BaseModel
from contextlib import AsyncExitStack
import ollama


class MCPClient:
    def __init__(self):
        self.session: ClientSession | None = None
        self.tools: list[MCPTool] = []
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self, server_script_path: str):
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
        )
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        read, write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()
        logger.info(f"Connected to MCP server: {server_script_path}")

        await self.refresh_tools()

    async def refresh_tools(self):
        if not self.session:
            raise RuntimeError("Not connected to a server")

        response = await self.session.list_tools()
        self.tools = response.tools
        logger.info(f"Found {len(self.tools)} tools")
        for tool in self.tools:
            logger.debug(f"  - {tool.name}: {tool.description}")

    def get_openai_tools(self) -> list[dict]:
        return [t.model_dump() for t in format_tools(self.tools)]

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        if not self.session:
            raise RuntimeError("Not connected to a server")

        logger.info(f"Calling tool: {tool_name} with args: {arguments}")
        result = await self.session.call_tool(tool_name, arguments)

        content_parts = []
        for content in result.content:
            if hasattr(content, 'text'):
                content_parts.append(content.text)

        return "\n".join(content_parts)

    async def close(self):
        await self.exit_stack.aclose()
        self.session = None
        self.tools = []
        logger.info("MCP client connection closed")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()



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

    async with MCPClient() as client:
        await client.connect_to_server("kubectl_mcp.py")

        tools = client.get_openai_tools()

        messages = [{"role": "user", "content": "Show me what nodes are in my kubernetes cluster"}]
        response = chat_with_tool("mistral-nemo:latest", messages, tools)

        if response and response.message.tool_calls:
            for tool_call in response.message.tool_calls:
                tool_name = tool_call.function.name
                arguments = tool_call.function.arguments
                result = await client.call_tool(tool_name, arguments)
                print(f"Tool {tool_name} result:\n{result}")
        else:
            print(response.message.content if response else "No response")

if __name__ == "__main__":
    asyncio.run(main())
