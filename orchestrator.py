from __future__ import annotations
from typing import Dict, Any, Optional, List
from models import AgentInvokeRequest, AgentInvokeResponse, ToolsListResult, CatalogItem, CatalogResponse, Tool
from mcp_client import mcp_tools_list, mcp_tools_call
from settings import settings
import re

_POLICY = (
    "Policy: If server+tool are specified, call directly. Otherwise, fetch all servers' tool catalogs, "
    "then pick the first tool whose name/title/description matches keywords from the message. "
    "If no match, return the aggregated catalog without calling anything."
)

async def aggregate_catalog() -> CatalogResponse:
    items: List[CatalogItem] = []
    for srv in settings.MCP_SERVERS:
        try:
            resp = await mcp_tools_list(srv.url, srv.api_key)
            tools = ToolsListResult(**resp.result).tools
            for t in tools:
                items.append(CatalogItem(server=srv.name, tool=t))
        except Exception as e:
            # Represent failures as a pseudo-tool so callers can see availability
            items.append(CatalogItem(server=srv.name, tool=Tool(name="__error__", title="Server error", description=str(e))))
    return CatalogResponse(items=items)

def _score(text: str, msg_words: set[str]) -> int:
    t = (text or "").lower()
    return sum(1 for w in msg_words if w and w in t)

async def select_tool(message: str, catalog: CatalogResponse) -> Optional[tuple[str, str]]:
    words = set(re.findall(r"[a-zA-Z_]+", message.lower()))
    best = None
    best_score = 0
    for item in catalog.items:
        t = item.tool
        hay = " ".join(filter(None, [t.name, t.title or "", t.description or ""]))
        score = _score(hay, words)
        if score > best_score and t.name != "__error__":
            best_score = score
            best = (item.server, t.name)
    return best

async def run_agent(payload: AgentInvokeRequest) -> AgentInvokeResponse:
    # Direct call if specified
    if payload.server and payload.tool:
        srv = next((s for s in settings.MCP_SERVERS if s.name == payload.server), None)
        if not srv:
            return AgentInvokeResponse(server_called=None, tool_called=None, tool_arguments={}, tool_result={"error": f"Unknown server '{payload.server}'"}, policy=_POLICY, catalog_returned=True)
        resp = await mcp_tools_call(srv.url, srv.api_key, payload.tool, payload.arguments)
        return AgentInvokeResponse(server_called=srv.name, tool_called=payload.tool, tool_arguments=payload.arguments, tool_result=resp.result, policy=_POLICY, catalog_returned=False)

    # Build catalog
    catalog = await aggregate_catalog()

    # No message? Return catalog
    if not payload.message:
        return AgentInvokeResponse(server_called=None, tool_called=None, tool_arguments={}, tool_result=catalog.model_dump(), policy=_POLICY, catalog_returned=True)

    # Pick best tool
    pick = await select_tool(payload.message, catalog)
    if not pick:
        return AgentInvokeResponse(server_called=None, tool_called=None, tool_arguments={}, tool_result=catalog.model_dump(), policy=_POLICY, catalog_returned=True)

    server_name, tool_name = pick
    srv = next((s for s in settings.MCP_SERVERS if s.name == server_name), None)
    if not srv:
        return AgentInvokeResponse(server_called=None, tool_called=None, tool_arguments={}, tool_result={"error": f"Selected server '{server_name}' not found"}, policy=_POLICY, catalog_returned=True)

    resp = await mcp_tools_call(srv.url, srv.api_key, tool_name, payload.arguments)
    return AgentInvokeResponse(server_called=server_name, tool_called=tool_name, tool_arguments=payload.arguments, tool_result=resp.result, policy=_POLICY, catalog_returned=False)
