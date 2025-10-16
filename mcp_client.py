from __future__ import annotations
import asyncio
import httpx
from typing import Any, Dict, Optional
from models import MCPJsonRpcRequest, MCPJsonRpcResponse

_DEFAULT_TIMEOUT = 15.0


async def _post_with_retries(
    url: str,
    json_payload: Dict[str, Any],
    headers: Dict[str, str],
    *,
    client: Optional[httpx.AsyncClient] = None,
    retries: int = 2,
) -> httpx.Response:
    delay = 0.2
    last_exc: Optional[Exception] = None

    for attempt in range(retries + 1):
        try:
            if client is None:
                async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as ac:
                    response = await ac.post(url, json=json_payload, headers=headers)
            else:
                response = await client.post(url, json=json_payload, headers=headers)

            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status is None or status < 500 or status >= 600:
                raise
            last_exc = exc
        except httpx.TimeoutException as exc:
            last_exc = exc

        if attempt == retries:
            if last_exc is not None:
                raise last_exc
            raise
        await asyncio.sleep(delay)
        delay = min(delay * 2, 1.5)


async def mcp_tools_list(base_url: str, api_key: Optional[str] = None,
                         client: Optional[httpx.AsyncClient] = None) -> MCPJsonRpcResponse:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    payload = MCPJsonRpcRequest(id=1, method="tools/list", params={}).model_dump()
    response = await _post_with_retries(base_url, payload, headers, client=client)
    return MCPJsonRpcResponse(**response.json())

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
    response = await _post_with_retries(base_url, payload, headers, client=client)
    return MCPJsonRpcResponse(**response.json())
