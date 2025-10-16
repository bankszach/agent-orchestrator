# Agent Orchestrator (FastAPI) — MCP Multi-Server Client

A compact FastAPI service that **discovers and invokes tools across multiple MCP servers**. Use it as a client-side
agent behind a UI or connect it to OpenAI Agent Builder as a single HTTP tool.

## Features
- Multiple MCP servers via `MCP_SERVERS` JSON env
- Aggregated tool catalog at `/catalog`
- Simple keyword-based routing: `/agent/invoke` chooses a tool by message content
- Direct addressing: specify `{ "server": "...", "tool": "...", "arguments": {...} }` to bypass policy
- Containerized; optional `docker-compose.yml` pairs with a local `fastapi-mcp`

## Quickstart (local)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app:app --reload --port 8080
```

### Test
```bash
# Catalog
curl -s http://localhost:8080/catalog | jq

# Naive routed call
curl -s -X POST http://localhost:8080/agent/invoke   -H 'content-type: application/json'   -d '{"message":"what time is it?","arguments":{"format":"%Y-%m-%d %H:%M:%S"}}' | jq

# Direct call
curl -s -X POST http://localhost:8080/agent/invoke   -H 'content-type: application/json'   -d '{"server":"clock","tool":"get_time","arguments":{}}' | jq
```

## Docker
```bash
docker build -t agent-orchestrator:latest .
docker run --rm -p 8080:8080 \  -e MCP_SERVERS='[{"name":"clock","url":"https://YOUR-CLOUD-RUN-URL/"}]' \  agent-orchestrator:latest
```

## Docker Compose (pair with fastapi-mcp)
The included `docker-compose.yml` shows how to run the orchestrator together with a local `fastapi-mcp` container.
Replace the image/build for `fastapi-mcp` to point at your server artifact.

```bash
docker compose up --build
```

## Env
- `MCP_SERVERS`: JSON list of `{name,url,api_key?}`
- `ALLOW_ORIGINS`: CORS allowlist (default `*`)
- `PORT`: service port (default 8080)
