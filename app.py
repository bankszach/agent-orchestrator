from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import AgentInvokeRequest, AgentInvokeResponse, CatalogResponse
from orchestrator import run_agent, aggregate_catalog
from settings import settings

app = FastAPI(title="Agent Orchestrator (MCP multi-server client)")

# CORS for dev & UIs
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOW_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.get("/config")
async def config_probe():
    return {
        "servers_configured": [s.name for s in settings.MCP_SERVERS],
        "origins": settings.ALLOW_ORIGINS,
    }

@app.get("/catalog", response_model=CatalogResponse)
async def catalog():
    return await aggregate_catalog()

@app.post("/agent/invoke", response_model=AgentInvokeResponse)
async def agent_invoke(payload: AgentInvokeRequest):
    return await run_agent(payload)
