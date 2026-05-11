"""
Bohrium Skill MCP Server - 结构化多轮对话版
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

server = Server("skill-boer-v2")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="bohr_chat",
            description=(
                "通过 Edge 浏览器访问 Bohrium AI 学术助手（结构化多轮对话版）。"
                "支持场景指定、格式控制、多轮对话上下文、结构化输出。"
                "自动复用 Edge 登录态，无需额外 token。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "要问的问题或消息内容（必填）",
                    },
                    "context": {
                        "type": "object",
                        "description": "场景上下文信息",
                        "properties": {
                            "scenario": {
                                "type": "string",
                                "enum": ["论文写作", "课题调研", "日常问答", "代码实现", "文献综述"],
                                "description": "使用场景",
                            },
                            "background": {
                                "type": "string",
                                "description": "补充背景信息，帮助AI更好理解需求",
                            },
                        },
                    },
                    "format": {
                        "type": "object",
                        "description": "输出格式控制",
                        "properties": {
                            "style": {
                                "type": "string",
                                "enum": ["academic", "casual", "technical", "summary"],
                                "description": "语言风格：academic(学术)/casual(通俗)/technical(技术)/summary(摘要)",
                                "default": "academic",
                            },
                            "detail": {
                                "type": "string",
                                "enum": ["brief", "standard", "detailed", "exhaustive"],
                                "description": "详细程度：brief(简要)/standard(标准)/detailed(详细)/exhaustive( exhaustive)",
                                "default": "standard",
                            },
                            "elements": {
                                "type": "array",
                                "items": {"type": "string", "enum": ["formula", "citation", "code", "example", "diagram"]},
                                "description": "必须包含的元素",
                            },
                            "language": {
                                "type": "string",
                                "enum": ["zh", "en", "bilingual"],
                                "description": "输出语言",
                                "default": "zh",
                            },
                            "max_length": {
                                "type": "integer",
                                "description": "回复最大长度（字符数）",
                            },
                        },
                    },
                    "conversation": {
                        "type": "array",
                        "description": "历史对话上下文（自动维护，无需手动传入）",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string", "enum": ["user", "assistant"]},
                                "content": {"type": "string"},
                            },
                        },
                    },
                    "clear_history": {
                        "type": "boolean",
                        "description": "是否清空历史对话，开启新会话",
                        "default": False,
                    },
                },
                "required": ["question"],
            },
        ),
        Tool(
            name="bohr_clear",
            description="清空当前对话历史，开启新会话",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "bohr_chat":
            question = arguments["question"]
            context = arguments.get("context")
            format_spec = arguments.get("format")
            conversation = arguments.get("conversation")
            clear_history = arguments.get("clear_history", False)

            client = BohriumClient(timeout=180, headless=True)
            result = client.chat(
                question=question,
                context=context,
                format_spec=format_spec,
                conversation=conversation,
                clear_history=clear_history,
            )

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]

        elif name == "bohr_clear":
            from bohrium_client import SESSION_FILE
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
            return [TextContent(
                type="text",
                text=json.dumps({"success": True, "message": "对话历史已清空"}, ensure_ascii=False)
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
