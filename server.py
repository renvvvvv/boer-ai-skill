import asyncio
import importlib.util
import json
import os
import sys
import urllib.request
import urllib.error
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from bohrium_browser_chat import BohriumBrowserChat

# 动态导入 skill-boer 目录下的模块（目录名含连字符，不能直接 import）
_skill_boer_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skill-boer")
_client_path = os.path.join(_skill_boer_dir, "bohrium_client.py")
_spec = importlib.util.spec_from_file_location("bohrium_client", _client_path)
_bohrium_client_module = importlib.util.module_from_spec(_spec)
sys.modules["bohrium_client"] = _bohrium_client_module
_spec.loader.exec_module(_bohrium_client_module)
BohriumEdgeClient = _bohrium_client_module.BohriumClient

ACCESS_KEY = os.environ.get("ACCESS_KEY", "")
BASE_URL = "https://openapi.dp.tech/openapi/v1"

server = Server("bohrium-mcp")


def api_call(method: str, path: str, params: dict = None, body: dict = None) -> dict:
    if params is None:
        params = {}
    params["accessKey"] = ACCESS_KEY

    query_parts = []
    for k, v in params.items():
        if v is not None:
            query_parts.append(f"{k}={urllib.request.quote(str(v))}")
    query_string = "&".join(query_parts)

    url = f"{BASE_URL}/{path}?{query_string}"
    headers = {"Accept": "application/json"}

    data = None
    if body:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, headers=headers, data=data, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        return {"code": e.code, "message": error_body, "error": str(e)}
    except Exception as e:
        return {"code": -1, "message": str(e), "error": str(e)}


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="bohr_project_list",
            description="List all Bohrium projects",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_size": {
                        "type": "integer",
                        "description": "Number of results per page (default 100)",
                        "default": 100,
                    },
                },
            },
        ),
        Tool(
            name="bohr_job_list",
            description="List Bohrium computing jobs with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by job status: running, pending, finish, fail, scheduling, stopping, stopped",
                    },
                    "job_group_id": {
                        "type": "integer",
                        "description": "Filter by job group ID",
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Number of results (default 10)",
                        "default": 10,
                    },
                },
            },
        ),
        Tool(
            name="bohr_job_describe",
            description="Get detailed information about a specific job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "integer",
                        "description": "The job ID to describe",
                    },
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="bohr_job_submit",
            description="Submit a new computing job to Bohrium",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": "Name of the job",
                    },
                    "command": {
                        "type": "string",
                        "description": "Command to execute on the compute node",
                    },
                    "project_id": {
                        "type": "integer",
                        "description": "Project ID to submit the job under",
                    },
                    "machine_type": {
                        "type": "string",
                        "description": "Machine type (e.g. c4_m15_1 * NVIDIA T4)",
                    },
                    "image_address": {
                        "type": "string",
                        "description": "Docker image address for the compute environment",
                    },
                    "log_file": {
                        "type": "string",
                        "description": "Path to log file for monitoring",
                    },
                    "input_directory": {
                        "type": "string",
                        "description": "Local input directory path (default ./)",
                    },
                    "result_path": {
                        "type": "string",
                        "description": "Path to auto-download results (e.g. /personal)",
                    },
                    "job_group_id": {
                        "type": "integer",
                        "description": "Job group ID to add this job to",
                    },
                    "nnode": {
                        "type": "integer",
                        "description": "Number of compute nodes (default 1)",
                        "default": 1,
                    },
                    "max_run_time": {
                        "type": "integer",
                        "description": "Max run time in minutes",
                    },
                },
                "required": ["job_name", "command", "project_id", "machine_type", "image_address"],
            },
        ),
        Tool(
            name="bohr_job_delete",
            description="Delete one or more jobs by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of job IDs to delete",
                    },
                },
                "required": ["job_ids"],
            },
        ),
        Tool(
            name="bohr_job_terminate",
            description="Terminate (stop early) one or more running jobs",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of job IDs to terminate",
                    },
                },
                "required": ["job_ids"],
            },
        ),
        Tool(
            name="bohr_job_log",
            description="Get log output for a specific job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "integer",
                        "description": "The job ID to get logs for",
                    },
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="bohr_node_list",
            description="List all Bohrium compute nodes",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by node status: started, paused, pending, waiting",
                    },
                },
            },
        ),
        Tool(
            name="bohr_node_stop",
            description="Stop (pause) a compute node",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "integer",
                        "description": "The node ID to stop",
                    },
                },
                "required": ["node_id"],
            },
        ),
        Tool(
            name="bohr_node_delete",
            description="Delete a compute node",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "integer",
                        "description": "The node ID to delete",
                    },
                },
                "required": ["node_id"],
            },
        ),
        Tool(
            name="bohr_image_list",
            description="List available software images for compute environments",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_size": {
                        "type": "integer",
                        "description": "Number of results (default 50)",
                        "default": 50,
                    },
                },
            },
        ),
        Tool(
            name="bohr_browser_chat",
            description="Chat with Bohrium AI academic assistant via browser automation. Supports fast (Auto) and pro (Pro) modes with lossless Markdown output.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The question or message to send to the AI assistant",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["fast", "pro", "mentor"],
                        "description": "模型模式：fast(快速), pro(专业), mentor(AI小导师)",
                        "default": "fast",
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Agent ID (default: sn for academic search)",
                        "default": "sn",
                    },
                    "scene": {
                        "type": "string",
                        "description": "Scene type (default: paper)",
                        "default": "paper",
                    },
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="bohr_browser_research",
            description="Deep research mode via browser automation. Use for comprehensive topic analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Research topic or question",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["fast", "pro"],
                        "description": "Model mode: fast or pro",
                        "default": "pro",
                    },
                },
                "required": ["topic"],
            },
        ),
        Tool(
            name="bohr_chat",
            description="通过 Edge 浏览器访问 Bohrium AI 学术助手。保留完整 Markdown/LaTeX/代码块输出。自动复用 Edge 登录态，无需额外 token。",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "要问的问题或消息内容",
                    },
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="bohr_health",
            description="健康检查：测试 Bohrium 访问是否正常",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "bohr_project_list":
            page_size = arguments.get("page_size", 100)
            result = api_call("GET", "project/list", {"pageSize": page_size})

        elif name == "bohr_job_list":
            params = {"pageSize": arguments.get("page_size", 10)}
            status = arguments.get("status")
            if status:
                status_map = {
                    "running": "running",
                    "pending": "pending",
                    "finish": "finish",
                    "fail": "fail",
                    "scheduling": "scheduling",
                    "stopping": "stopping",
                    "stopped": "stopped",
                }
                mapped = status_map.get(status, status)
                params[mapped] = "true"
            job_group_id = arguments.get("job_group_id")
            if job_group_id:
                params["jobGroupId"] = job_group_id
            result = api_call("GET", "job/list", params)

        elif name == "bohr_job_describe":
            job_id = arguments["job_id"]
            result = api_call("GET", "job/describe", {"jobId": job_id})

        elif name == "bohr_job_submit":
            body = {
                "jobName": arguments["job_name"],
                "command": arguments["command"],
                "projectId": arguments["project_id"],
                "machineType": arguments["machine_type"],
                "imageAddress": arguments["image_address"],
            }
            optional_fields = [
                ("logFile", "log_file"),
                ("inputDirectory", "input_directory"),
                ("resultPath", "result_path"),
                ("jobGroupId", "job_group_id"),
                ("nnode", "nnode"),
                ("maxRunTime", "max_run_time"),
            ]
            for api_field, arg_field in optional_fields:
                if arguments.get(arg_field):
                    body[api_field] = arguments[arg_field]
            result = api_call("POST", "job/submit", body=body)

        elif name == "bohr_job_delete":
            job_ids = arguments["job_ids"]
            result = api_call("DELETE", "job/delete", {"jobIds": ",".join(map(str, job_ids))})

        elif name == "bohr_job_terminate":
            job_ids = arguments["job_ids"]
            result = api_call("POST", "job/terminate", {"jobIds": ",".join(map(str, job_ids))})

        elif name == "bohr_job_log":
            job_id = arguments["job_id"]
            result = api_call("GET", "job/log", {"jobId": job_id})

        elif name == "bohr_node_list":
            params = {}
            status = arguments.get("status")
            if status:
                status_map = {
                    "started": "started",
                    "paused": "paused",
                    "pending": "pending",
                    "waiting": "waiting",
                }
                mapped = status_map.get(status, status)
                params[mapped] = "true"
            result = api_call("GET", "node/list", params)

        elif name == "bohr_node_stop":
            node_id = arguments["node_id"]
            result = api_call("POST", "node/stop", {"nodeId": node_id})

        elif name == "bohr_node_delete":
            node_id = arguments["node_id"]
            result = api_call("DELETE", "node/delete", {"nodeId": node_id})

        elif name == "bohr_image_list":
            page_size = arguments.get("page_size", 50)
            result = api_call("GET", "image/list", {"pageSize": page_size})

        elif name == "bohr_browser_chat":
            message = arguments["message"]
            mode = arguments.get("mode", "fast")
            agent_id = arguments.get("agent_id", "sn")
            scene = arguments.get("scene", "paper")
            chat = BohriumBrowserChat()
            result = chat.chat(message, mode=mode, agent_id=agent_id, scene=scene)

        elif name == "bohr_browser_research":
            topic = arguments["topic"]
            mode = arguments.get("mode", "pro")
            chat = BohriumBrowserChat()
            result = chat.deep_research(topic, mode=mode)

        elif name == "bohr_chat":
            message = arguments["message"]
            client = BohriumEdgeClient(timeout=180, headless=True)
            result = client.chat(message)

        elif name == "bohr_health":
            client = BohriumEdgeClient(timeout=30, headless=True)
            result = client.health_check()

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())