from __future__ import annotations
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
import os, json

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
        if not v:
            raw = os.getenv("MCP_SERVERS", "[]")
            try:
                v = json.loads(raw)
            except Exception:
                v = []
        return v

settings = Settings()
