# mcp_facade.py
import json
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import FastMCP

# Public URL of THIS service (no trailing slash)
ORCH_BASE = "https://agent-orchestrator-596716165839.us-west2.run.app"

mcp = FastMCP("agent-orchestrator")


async def _invoke(payload: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(f"{ORCH_BASE}/agent/invoke", json=payload)
        try:
            body = r.json()
        except Exception:
            body = {"status": r.status_code, "text": r.text}
        return {"status": r.status_code, "data": body}


# Register ONE meta-tool that delegates to your existing REST router.
# Call with either:
#  - {"direct": "server.tool", "args": {...}}
#  - {"query": "natural language", "args": {...} }
@mcp.tool("orchestrator.invoke")
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


# Expose ASGI app for MCP over SSE
mcp_asgi_app = mcp.sse_app()
