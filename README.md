# Agent Orchestrator (FastAPI) — MCP Multi-Server Client

A compact FastAPI service that **discovers and invokes tools across multiple MCP servers**. Use it as a client-side
agent behind a UI or connect it to OpenAI Agent Builder as a single HTTP tool.

## Features
- Multiple MCP servers via `MCP_SERVERS` JSON env
- Aggregated tool catalog at `/catalog`
- Simple keyword-based routing: `/agent/invoke` chooses a tool by message content
- Direct addressing: specify `{ "server": "...", "tool": "...", "arguments": {...} }` to bypass policy
- Debug endpoints for ops: `/config/raw` (raw env slice) and `/version` (commit metadata)
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
- `COMMIT_SHA`: optional, surfaced at `/version` (default `unknown`)

## Cloud Run Deployment
1. **Console UI**
   - Navigate to *Cloud Run → agent-orchestrator → Edit & deploy new revision → Variables & Secrets → Environment variables*.
   - Add/update the variables you need (e.g. `MCP_SERVERS`, `COMMIT_SHA`).
2. **Example env payloads**
   - Single-line JSON (multiple servers):  
     ```json
     [{"name":"clock","url":"https://mcp-clock.run.app/"},{"name":"calendar","url":"https://mcp-calendar.run.app/","api_key":"$CAL_API_KEY"}]
     ```
   - Base64 works too, but plain JSON is easier to debug.
3. **gcloud CLI**
   ```bash
   gcloud run services update agent-orchestrator \
     --region us-west2 \
     --set-env-vars='MCP_SERVERS=[{"name":"clock","url":"https://mcp-test-service-596716165839.us-west2.run.app/"}]'
   ```
   - To expose the deployed commit:
     ```bash
     gcloud run services update agent-orchestrator \
       --region us-west2 \
       --set-env-vars=COMMIT_SHA=$(git rev-parse --short=12 HEAD)
     ```

## Post-Deploy Checks
```bash
curl -s https://<ORCH-URL>/config/raw | jq           # confirm raw MCP_SERVERS
curl -s https://<ORCH-URL>/config | jq               # parsed servers list
curl -s https://<ORCH-URL>/catalog | jq              # tool availability (ok vs __error__)
curl -s -X POST https://<ORCH-URL>/agent/invoke \
  -H 'content-type: application/json' \
  -d '{"server":"clock","tool":"get_time","arguments":{"format":"%Y-%m-%d %H:%M:%S"}}' | jq
curl -s https://<ORCH-URL>/version                   # commit metadata
```
