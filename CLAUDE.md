# Staker Agent

Ethereum validator node deployment and operations tool. CLI + Web UI + Telegram bot + AI Agent.

## Quick Start

```bash
# Backend
source .venv/bin/activate
pip install -r requirements.txt
pip install -r web/backend/requirements.txt

# Frontend
cd web/frontend && npm install && cd ../..

# Run (Flask + Telegram bot)
python3 web/backend/main.py

# Run (Flask only, no Telegram)
python3 web/backend/app.py
```

## Architecture

Two-loop agent design based on [learn.shareai.run](https://learn.shareai.run/en/) patterns:

```
core/agent/tools.py          Unified Tool Registry (s02) — 12 tools
                             Shared by both loops
                    ┌────────────┴────────────┐
          Monitor Loop (s11)          Chat Loop (s01)
          core/agent/monitor.py       services/agent.py
          Rules-driven, daemon        LLM-driven, on-demand
          Auto-restarts, alerts       TodoWrite (s03) for multi-step ops
                    │    notif_queue (s08)    │
                    └────────────┬────────────┘
                          Shared State
                       core/agent/state.py
```

**Monitor Loop**: Background daemon that checks node health every 60s. Uses deterministic rules (no LLM). Auto-restarts crashed containers, sends Telegram alerts, escalates to human after N failures.

**Chat Loop**: LLM-powered (OpenRouter). Before each LLM call, drains monitor notifications into context (s08 pattern) and micro-compacts old tool results (s06 pattern). Uses TodoWrite (s03) to track multi-step operations like deployment.

## Project Structure

```
core/                          Pure business logic, no Flask dependency
  agent/
    tools.py                   Tool Registry: dispatch map name -> handler (12 tools)
    state.py                   AgentState: shared between both loops
    todo.py                    s03: TodoManager for multi-step task tracking
    monitor.py                 MonitorLoop: autonomous health monitoring
    notifier.py                Event formatting (MarkdownV2)
    skills/                    s05: on-demand knowledge (staking.md, lido-csm.md, troubleshooting.md)
  monitor/
    health.py                  HealthMonitor: stateless check functions
  node/status.py               StatusMonitor: Docker/RPC data collection
  config/                      Network config (networks.yaml)
  deploy/                      Deployment orchestration
  docker/                      Docker/eth-docker management
  keys/                        Validator key generation (pexpect)

web/backend/
  main.py                      Unified entrypoint (Flask daemon + Telegram main thread)
  app.py                       Flask-only entrypoint
  staker_backend/
    __init__.py                App factory: create_app()
    services/
      container.py             ServiceContainer dataclass (DI)
      __init__.py              init_services() — wires everything including MonitorLoop
      agent.py                 Chat Loop: LLM streaming + tool execution
    routes/                    REST blueprints (/api/*)
    repositories/              Docker + filesystem access
    jobs/                      Background job manager
  telegram_bot/
    bot.py                     Bot factory + command registration
    handlers.py                /start /status /health /reset + chat
    alerts.py                  TelegramAlertSender (httpx direct)
    formatting.py              MarkdownV2 utilities
  websocket/                   Socket.IO event handlers

web/frontend/                  React + Vite + Tailwind
  src/pages/Dashboard.tsx      Main dashboard with health monitor
  src/hooks/useAgentChat.ts    Chat WebSocket hook
  src/hooks/useHealthMonitor.ts Health WebSocket hook
```

## Key Patterns

### Adding a new tool
1. Add handler function in `core/agent/tools.py`: `def handle_foo(tool_input, ctx) -> dict`
2. Add to `TOOL_HANDLERS` dispatch map
3. Add OpenAI function schema to `TOOL_DEFINITIONS`
4. Done. Both Monitor Loop and Chat Loop can now use it.

### Tool handler signature
```python
def handle_something(tool_input: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    # ctx.services       — Flask ServiceContainer (deployment handlers)
    # ctx.state          — AgentState (ops handlers)
    # ctx.status_monitor — StatusMonitor (health handlers)
    # ctx.todo           — TodoManager (task tracking, per-session)
    # ctx.eth_docker_path — ~/eth-docker
    return {"success": True, ...}
```

### TodoWrite (s03) — multi-step task tracking
The LLM uses the `todo` tool to create/update a task list before multi-step operations.
- Only one task can be `in_progress` at a time
- If 3+ turns pass without a `todo` update, a `<reminder>` is injected into tool results
- TodoManager is per-session (stored on `_Session.todo`), survives context compression
- The LLM should create a todo list at the start of deployment, then update after each step

### Adding a Telegram command
1. Add handler in `telegram_bot/handlers.py`
2. Register in `telegram_bot/bot.py` with CommandHandler
3. Use `context.bot_data["services"]` to access ServiceContainer

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `OPENROUTER_API_KEY` | (required for chat) | LLM API key |
| `OPENROUTER_MODEL` | `openrouter/free` | LLM model |
| `TELEGRAM_BOT_TOKEN` | (required for Telegram) | Bot authentication |
| `TELEGRAM_ALLOWED_CHAT_IDS` | (none = all) | Comma-separated ACL |
| `TELEGRAM_ALERT_CHAT_ID` | (none) | Chat ID for proactive alerts |
| `MONITOR_ENABLED` | `true` | Enable health monitoring |
| `MONITOR_CHECK_INTERVAL` | `60` | Seconds between health checks |
| `MONITOR_ALERT_COOLDOWN` | `300` | Seconds before re-alerting |
| `MONITOR_MAX_AUTO_ACTIONS` | `3` | Auto-restart limit before escalation |
| `STAKER_AGENT_ETH_DOCKER_PATH` | `~/eth-docker` | eth-docker install path |

## Conventions

- Python: type hints, dataclasses over dicts for structured data
- `core/` must not import from `web/` (no Flask dependency)
- Tool handlers return `{"success": bool, ...}` dicts
- Telegram formatting uses MarkdownV2 (escape with `escape_md()`)
- Health levels: `HealthLevel.HEALTHY`, `DEGRADED`, `CRITICAL` (enum in `core/monitor/health.py`)
- Monitor events flow: MonitorLoop -> notif_queue -> Chat Loop drains before LLM call
- TodoWrite: LLM creates task list via `todo` tool before multi-step ops; nag after 3 idle turns
- Chinese is the default UI language, but code/logs are in English

## Applied Agent Patterns (from learn.shareai.run)

| Pattern | Session | Where Applied |
|---------|---------|---------------|
| Agent Loop | s01 | `services/agent.py` — while True + tools + stop_reason |
| Tool Dispatch | s02 | `core/agent/tools.py` — TOOL_HANDLERS dict |
| TodoWrite | s03 | `core/agent/todo.py` — task tracking + nag reminder |
| Skills | s05 | `core/agent/skills/` — on-demand knowledge loading |
| Compact | s06 | `services/agent.py` — `_micro_compact()` on old tool results |
| Background Notifications | s08 | `services/agent.py` — `_drain_notifications()` before LLM call |
| Autonomous Agent | s11 | `core/agent/monitor.py` — rules-driven background loop |
