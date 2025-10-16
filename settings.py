from __future__ import annotations
from pydantic import BaseModel, field_validator
from typing import Optional, List
import base64
import os
import json

class MCPServer(BaseModel):
    name: str
    url: str
    api_key: Optional[str] = None

class Settings(BaseModel):
    # JSON list of {name,url,api_key?}
    MCP_SERVERS: List[MCPServer] = []
    PORT: int = int(os.getenv("PORT", "8080"))
    ALLOW_ORIGINS: str = os.getenv("ALLOW_ORIGINS", "*")

    @field_validator("MCP_SERVERS", mode="before")
    @classmethod
    def parse_servers(cls, v):
        if isinstance(v, list):
            return v

        raw = os.getenv("MCP_SERVERS", "")
        if not raw:
            print("[settings] MCP_SERVERS env is empty")
            return []

        try:
            return json.loads(raw)
        except Exception as e_json:
            try:
                decoded = base64.b64decode(raw).decode("utf-8", "ignore")
                return json.loads(decoded)
            except Exception as e_b64:
                head = raw[:120].replace("\n", "\\n")
                print(
                    "[settings] Failed to parse MCP_SERVERS; "
                    f"head={head!r}; json_err={type(e_json).__name__}; b64_err={type(e_b64).__name__}"
                )
                return []

settings = Settings()
_boot_names = [
    s.get("name") if isinstance(s, dict) else getattr(s, "name", None)
    for s in settings.MCP_SERVERS
]
print(f"[boot] servers configured count={len(_boot_names)} names={_boot_names}")
