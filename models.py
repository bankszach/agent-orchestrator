from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class Tool(BaseModel):
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    inputSchema: Dict[str, Any] = Field(default_factory=dict)
    outputSchema: Dict[str, Any] = Field(default_factory=dict)

class ToolsListResult(BaseModel):
    tools: List[Tool]

class MCPJsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: int | str
    method: str
    params: Dict[str, Any] | None = None

class MCPJsonRpcResponse(BaseModel):
    jsonrpc: str
    id: int | str | None
    result: Any | None = None
    error: Dict[str, Any] | None = None

class AgentInvokeRequest(BaseModel):
    message: Optional[str] = None
    # Target specific server/tool (optional)
    server: Optional[str] = None
    tool: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)

class AgentInvokeResponse(BaseModel):
    server_called: Optional[str] = None
    tool_called: Optional[str] = None
    tool_arguments: Dict[str, Any] = Field(default_factory=dict)
    tool_result: Any | None = None
    policy: str
    catalog_returned: bool = False

class CatalogItem(BaseModel):
    server: str
    tool: Tool

class CatalogResponse(BaseModel):
    items: List[CatalogItem] = Field(default_factory=list)
