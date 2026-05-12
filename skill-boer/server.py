"""
Bohrium Skill MCP Server - 极简稳定版
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from bohrium_client import BohriumClient

server = Server("skill-boer")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="bohr_chat",
            description=(
                "通过 Edge 浏览器访问 Bohrium (玻尔) AI 学术助手。"
                "自动复用 Edge 登录态，无需额外 token。"
                "流程：打开 bohrium.com → 填入问题 → 发送 → 收集 AI 回复"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "要问的问题或消息内容（必填）",
                    },
                },
                "required": ["message"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "bohr_chat":
            message = arguments["message"]
            client = BohriumClient(timeout=180, headless=True)
            result = client.chat(message)

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        import traceback
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }, indent=2, ensure_ascii=False)
        )]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
