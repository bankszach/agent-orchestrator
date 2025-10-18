from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import httpx
from mcp.server.fastmcp import FastMCP

# Base URL for the orchestrator REST facade (no trailing slash).
# Defaults to the deployed Cloud Run instance but can be overridden in env.
ORCH_BASE = os.getenv(
    "ORCH_BASE",
    "https://agent-orchestrator-596716165839.us-west2.run.app",
)

# ----- Build the MCP server -----
mcp = FastMCP("agent-orchestrator")


async def _fetch_catalog() -> Dict[str, Any]:
    """Fetch the merged catalog from the REST endpoint."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{ORCH_BASE}/catalog")
        resp.raise_for_status()
        return resp.json()


async def _invoke_direct(
    server_tool: str, args: Dict[str, Any] | None
) -> Dict[str, Any]:
    """Invoke a downstream tool directly via the REST router."""
    payload = {"direct": server_tool, "args": args or {}}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{ORCH_BASE}/agent/invoke", json=payload)
        try:
            data = resp.json()
        except Exception:
            data = {"status": resp.status_code, "text": resp.text}
        return {"status": resp.status_code, "data": data}


@mcp.list_tools
async def list_tools() -> List[Dict[str, Any]]:
    """Return the merged downstream tools as native MCP tools."""
    catalog = await _fetch_catalog()
    tools: List[Dict[str, Any]] = []
    for tool in catalog.get("tools", []):
        name = f'{tool["server"]}.{tool["name"]}'
        description = tool.get("description", "")
        schema = tool.get("input_schema", {"type": "object"})
        tools.append(
            {
                "name": name,
                "description": description,
                "inputSchema": schema,
            }
        )
    return tools


@mcp.call_tool
async def call_tool(name: str, arguments: Dict[str, Any] | None = None):
    """Directly invoke the selected downstream tool via the REST router."""
    result = await _invoke_direct(name, arguments or {})
    pretty = json.dumps(result, indent=2, ensure_ascii=False)
    return {
        "content": [{"type": "text", "text": pretty}],
        "isError": result.get("status", 200) >= 400,
    }


# Expose an ASGI app that speaks MCP over Server-Sent Events (SSE)
# ASGI app is mounted in app.py at /mcp.
mcp_asgi_app = mcp.sse_app()
