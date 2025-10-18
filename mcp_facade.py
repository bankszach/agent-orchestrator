# mcp_facade.py
import json
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import FastMCP

ORCH_BASE = "https://agent-orchestrator-596716165839.us-west2.run.app"

mcp = FastMCP("agent-orchestrator")


async def _invoke(payload: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f"{ORCH_BASE}/agent/invoke", json=payload)
        try:
            body = response.json()
        except Exception:
            body = {"status": response.status_code, "text": response.text}
        return {"status": response.status_code, "data": body}


# Register ONE reliable meta-tool that delegates to your REST router.
# You can call it with either:
# { "direct": "server.tool", "args": {...} }  OR  { "query": "natural language" }
@mcp.tool(
    "orchestrator.invoke",
    desc="Route a query or a direct server.tool to the downstream MCP via the Agent Orchestrator.",
)
async def orchestrator_invoke(
    direct: Optional[str] = None,
    query: Optional[str] = None,
    args: Optional[Dict[str, Any]] = None,
) -> str:
    if not direct and not query:
        return "error: provide either 'direct' (e.g., 'clock.get_time') or 'query'."

    payload: Dict[str, Any] = {}
    if direct:
        payload["direct"] = direct
        payload["args"] = args or {}
    else:
        payload["query"] = query
        if args:
            payload["args"] = args

    result = await _invoke(payload)
    return json.dumps(result, indent=2, ensure_ascii=False)


# Expose an ASGI app that serves MCP over SSE
mcp_asgi_app = mcp.sse_app()
