from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List
import base64
import json
import os


class MCPServer(BaseModel):
    name: str
    url: str
    api_key: Optional[str] = None


class Settings(BaseModel):
    MCP_SERVERS: List[MCPServer] = []
    PORT: int = int(os.getenv("PORT", "8080"))
    ALLOW_ORIGINS: str = os.getenv("ALLOW_ORIGINS", "*")


def _parse_servers_from_env() -> List[MCPServer]:
    raw = os.getenv("MCP_SERVERS", "")
    if not raw:
        print("[settings] MCP_SERVERS env is empty")
        return []

    def _coerce(data: List[dict | MCPServer]) -> List[MCPServer]:
        servers: List[MCPServer] = []
        for item in data:
            if isinstance(item, MCPServer):
                servers.append(item)
            elif isinstance(item, dict):
                servers.append(MCPServer(**item))
            else:
                raise TypeError(f"Unsupported server entry type: {type(item).__name__}")
        return servers

    try:
        data = json.loads(raw)
        return _coerce(data)
    except Exception as e_json:
        try:
            decoded = base64.b64decode(raw).decode("utf-8", "ignore")
            data = json.loads(decoded)
            return _coerce(data)
        except Exception as e_b64:
            head = raw[:120].replace("\n", "\\n")
            print(
                "[settings] Failed to parse MCP_SERVERS; "
                f"head={head!r}; json_err={type(e_json).__name__}; b64_err={type(e_b64).__name__}"
            )
            return []


settings = Settings()
if not settings.MCP_SERVERS:
    settings.MCP_SERVERS = _parse_servers_from_env()

print(
    f"[boot] servers configured count={len(settings.MCP_SERVERS)} "
    f"names={[s.name for s in settings.MCP_SERVERS]}"
)
