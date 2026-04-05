# hermes-a2a

An [Agent-to-Agent (A2A) protocol](https://a2a-protocol.org/) server that bridges to the local [Hermes agent](https://github.com/NousResearch/hermes-agent). Any A2A-compatible client can discover and communicate with Hermes through this server.

## How it works

```
A2A Client  ──JSON-RPC 2.0──►  hermes-a2a (port 9000)  ──OpenAI API──►  Hermes (port 8642)
```

- Exposes `/.well-known/agent-card.json` for A2A discovery
- Accepts `message/send` and `message/stream` JSON-RPC methods
- Maps `context_id` → `X-Hermes-Session-Id` for conversation continuity
- Streams Hermes SSE responses back as A2A artifact events

## Setup

```bash
make init
# Edit .env and set HERMES_API_KEY (same as API_SERVER_KEY in Hermes config)
```

## Running

```bash
make start    # starts on port 9000
make stop     # stop the server
make restart  # stop then start
```

## Configuration

Edit `.env` (created from `.env.example` during `make init`):

| Variable | Default | Description |
|----------|---------|-------------|
| `HERMES_URL` | `http://127.0.0.1:8642` | Hermes gateway URL |
| `HERMES_API_KEY` | *(required)* | Bearer token (`API_SERVER_KEY` in Hermes) |
| `A2A_HOST` | `0.0.0.0` | Bind address |
| `A2A_PORT` | `9000` | Listen port |
| `A2A_LOG_LEVEL` | `info` | Log level |
| `HERMES_TIMEOUT` | `120.0` | Request timeout in seconds |

## Testing

```bash
# Verify the server is running
curl http://localhost:9000/.well-known/agent-card.json | jq .

# Send a message (non-streaming)
curl -X POST http://localhost:9000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Hello Hermes!"}],
        "messageId": "msg-001"
      }
    }
  }'

# Send a streaming message
curl -X POST http://localhost:9000/ \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "message/stream",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "What tools do you have?"}],
        "messageId": "msg-002"
      }
    }
  }'

# Run unit tests
make test
```

## Project structure

```
hermes_a2a/
├── config.py          # pydantic-settings configuration
├── hermes_client.py   # async httpx wrapper for Hermes API
├── agent_card.py      # A2A agent card / capabilities descriptor
├── executor.py        # HermesAgentExecutor — core bridge logic
└── __main__.py        # entry point
```
