from __future__ import annotations

import base64
import json
import os
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPServer(BaseModel):
    name: str
    url: str
    api_key: Optional[str] = None


def _coerce_servers(data: List[dict | MCPServer]) -> List[MCPServer]:
    servers: List[MCPServer] = []
    for item in data:
        if isinstance(item, MCPServer):
            servers.append(item)
        elif isinstance(item, dict):
            servers.append(MCPServer(**item))
        else:
            raise TypeError(f"Unsupported server entry type: {type(item).__name__}")
    return servers


def _parse_servers(raw: str) -> List[MCPServer]:
    if not raw:
        print("[settings] MCP_SERVERS env is empty")
        return []

    try:
        data = json.loads(raw)
        return _coerce_servers(data)
    except Exception as e_json:
        try:
            decoded = base64.b64decode(raw).decode("utf-8", "ignore")
            data = json.loads(decoded)
            return _coerce_servers(data)
        except Exception as e_b64:
            head = raw[:120].replace("\n", "\\n")
            print(
                "[settings] Failed to parse MCP_SERVERS; "
                f"head={head!r}; json_err={type(e_json).__name__}; b64_err={type(e_b64).__name__}"
            )
            return []


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ALLOW_ORIGINS: str = "*"
    MCP_SERVERS: List[MCPServer] = Field(default_factory=list)
    PORT: int = Field(default=8080)

    @field_validator("ALLOW_ORIGINS", mode="before")
    @classmethod
    def _default_allow_origins(cls, value: str | None) -> str:
        if value is None or value == "":
            return "*"
        return value

    @field_validator("MCP_SERVERS", mode="before")
    @classmethod
    def _parse_servers_field(cls, value):
        if value in (None, "", []):
            raw = os.getenv("MCP_SERVERS", "")
            if not raw:
                return []
            value = raw

        if isinstance(value, str):
            return _parse_servers(value)

        if isinstance(value, list):
            return _coerce_servers(value)

        raise TypeError(f"Unsupported MCP_SERVERS type: {type(value).__name__}")


settings = Settings()

print(
    f"[boot] servers configured count={len(settings.MCP_SERVERS)} "
    f"names={[s.name for s in settings.MCP_SERVERS]}"
)
