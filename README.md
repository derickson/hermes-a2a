# hermes-a2a

<img width="1344" height="752" alt="image" src="https://github.com/user-attachments/assets/d462e26d-507f-4213-843b-1b05f558d4ea" />


An [Agent-to-Agent (A2A) protocol](https://a2a-protocol.org/) server that bridges to the local Hermes agent. Any A2A-compatible client can discover and communicate with Hermes through this server without needing to speak the OpenAI API directly.

## How it works

```
A2A Client  ──JSON-RPC 2.0──►  hermes-a2a (port 9000)  ──OpenAI API──►  Hermes (port 8642)
```

- Exposes `/.well-known/agent-card.json` for A2A discovery
- Accepts `message/send` and `message/stream` JSON-RPC methods
- Maps `context_id` → `X-Hermes-Session-Id` for conversation continuity
- Streams Hermes SSE responses back as A2A artifact events

## Prerequisites

### 1. Enable the Hermes API server

The Hermes gateway must have its API server platform enabled. Add to `~/.hermes/.env`:

```bash
API_SERVER_ENABLED=true
API_SERVER_KEY=your-secret-key   # generate with: openssl rand -hex 32
```

Then restart the Hermes gateway:

```bash
hermes gateway restart
```

Verify it's listening:

```bash
curl http://127.0.0.1:8642/health
# → {"status": "ok", "platform": "hermes-agent"}
```

### 2. Install hermes-a2a

```bash
make init
```

This creates a virtual environment at `~/dev/.venvs/hermes-a2a`, installs dependencies, and copies `.env.example` to `.env`.

Edit `.env` and set `HERMES_API_KEY` to the same value as `API_SERVER_KEY` in Hermes:

```bash
HERMES_API_KEY=your-secret-key
```

## Running as a service

hermes-a2a is designed to run as a persistent macOS launchd service that starts on login and restarts automatically on crash.

```bash
make service-load     # register with launchd and start (run once)
```

The service will now start automatically on every login. To manage it:

```bash
make service-start    # start the service
make service-stop     # stop the service
make service-restart  # stop then start
make service-unload   # deregister (disables auto-start)
make logs             # tail the log file
```

Logs are written to `logs/hermes-a2a.log` and `logs/hermes-a2a.error.log`.

The launchd plist is at `~/Library/LaunchAgents/com.dave.hermes-a2a.plist`.

## Configuration

Edit `.env` (created from `.env.example` during `make init`):

| Variable | Default | Description |
|----------|---------|-------------|
| `HERMES_URL` | `http://127.0.0.1:8642` | Hermes gateway base URL |
| `HERMES_API_KEY` | *(required)* | Must match `API_SERVER_KEY` in `~/.hermes/.env` |
| `HERMES_MODEL` | `hermes-agent` | Model name sent to Hermes |
| `HERMES_TIMEOUT` | `120.0` | Per-request timeout in seconds |
| `A2A_HOST` | `0.0.0.0` | Bind address |
| `A2A_PORT` | `9000` | Listen port |
| `A2A_LOG_LEVEL` | `info` | Log level (`debug`, `info`, `warning`, `error`) |

## Running without the service

For development or one-off use:

```bash
make start    # foreground, Ctrl+C to stop
make stop     # kill by process name
make restart  # stop then start
```

## Verifying

```bash
# Agent card (confirms server is up and discoverable)
curl http://localhost:9000/.well-known/agent-card.json | jq .

# Send a message (blocking)
curl -s -X POST http://localhost:9000/ \
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
  }' | jq .

# Stream a response
curl -s -X POST http://localhost:9000/ \
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

logs/
├── hermes-a2a.log         # stdout (service mode)
└── hermes-a2a.error.log   # stderr (service mode)
```
