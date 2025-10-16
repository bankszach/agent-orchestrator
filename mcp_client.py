from __future__ import annotations
import httpx
from typing import Any, Dict, Optional
from models import MCPJsonRpcRequest, MCPJsonRpcResponse

async def mcp_tools_list(base_url: str, api_key: Optional[str] = None,
                         client: Optional[httpx.AsyncClient] = None) -> MCPJsonRpcResponse:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    payload = MCPJsonRpcRequest(id=1, method="tools/list", params={}).model_dump()
    if client is None:
        async with httpx.AsyncClient(timeout=15.0) as ac:
            r = await ac.post(base_url, json=payload, headers=headers)
    else:
        r = await client.post(base_url, json=payload, headers=headers)
    r.raise_for_status()
    return MCPJsonRpcResponse(**r.json())

async def mcp_tools_call(base_url: str, api_key: Optional[str], name: str,
                         arguments: Dict[str, Any] | None = None,
                         client: Optional[httpx.AsyncClient] = None) -> MCPJsonRpcResponse:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    payload = MCPJsonRpcRequest(
        id=2,
        method="tools/call",
        params={"name": name, "arguments": arguments or {}}
    ).model_dump()
    if client is None:
        async with httpx.AsyncClient(timeout=15.0) as ac:
            r = await ac.post(base_url, json=payload, headers=headers)
    else:
        r = await client.post(base_url, json=payload, headers=headers)
    r.raise_for_status()
    return MCPJsonRpcResponse(**r.json())
