# Hackathon Submission Disclosure

This document discloses the scope of work done during ETHGlobal OpenAgents
(2026-04-24 to 2026-05-06) versus pre-existing work in this repository.

## TL;DR

This project was started on **2025-10-02**, predating the hackathon by ~7 months.
We are submitting it for **Showcase only** and explicitly **not applying** for
Partner Prizes or Finalist judging, in compliance with ETHGlobal's
"Start Fresh" rule.

During the hackathon we focused on **production hardening** — security,
resilience, and operability — not new features.

## Timeline

| Event | Date | Commit |
|-------|------|--------|
| Project started | 2025-10-02 | `8e82f33` |
| Agent architecture added | 2026-03-23 | `a3104f9` |
| Pre-hackathon HEAD | 2026-03-24 | `aed629f` |
| Hackathon began | 2026-04-24 | — |
| First hackathon commit | 2026-05-03 | `1ef0fe9` |
| Last hackathon commit | 2026-05-03 | `038cb9f` |
| Submission deadline | 2026-05-03 12:00 EDT | — |

## Pre-existing scope

The following components existed before the hackathon and are reused as-is
or with minor edits:

| Directory | Description |
|-----------|-------------|
| `core/agent/tools.py` | Unified tool registry (14 tools) |
| `core/agent/monitor.py` | Deterministic health monitor loop |
| `core/agent/memory.py` | Persistent memory with hybrid search |
| `core/agent/composer.py` | LLM message assembly via injector chain |
| `core/agent/todo.py` | Multi-step task tracking (TodoWrite) |
| `core/agent/skills/` | On-demand knowledge (staking, Lido CSM, troubleshooting) |
| `core/monitor/health.py` | Stateless health check functions |
| `core/node/status.py` | Docker + RPC data collection |
| `core/deploy/manager.py` | Deployment orchestration |
| `core/docker/` | Docker / eth-docker management |
| `core/keys/manager.py` | Validator key generation (pexpect) |
| `core/config/` | Network config + generator |
| `core/remote/` | SSH + Ansible remote deployment |
| `commands/` | CLI command handlers |
| `cli.py` | Click CLI entrypoint |
| `web/backend/staker_backend/services/agent.py` | Chat loop (LLM streaming + tool execution) — **heavily modified during hackathon** |
| `web/backend/staker_backend/routes/` | REST API blueprints |
| `web/backend/staker_backend/services/` | Flask service layer |
| `web/backend/telegram_bot/` | Telegram bot + alerts |
| `web/backend/websocket/` | Socket.IO handlers |
| `web/frontend/` | React + Vite + Tailwind dashboard |

## New work during the hackathon

50 files changed, **+2,340 / -132 lines** (~14% of the 16k-line codebase).
All commits are on 2026-05-03.

### P0a: Secret redaction pipeline + directed mnemonic delivery (`1ef0fe9`)
- `core/security/redact.py` — **NEW**: recursive redactor for mnemonic, password, API key, SSH key
- `core/security/__init__.py` — re-export
- `tests/test_redact_secrets.py` — **NEW**: 27 tests covering nested dicts, BIP-39 patterns, tool results

### P0b: Localhost binding + bearer token auth (`bfdc4c6`)
- `web/backend/staker_backend/auth.py` — **NEW**: `@require_auth` decorator, Socket.IO token check
- `web/backend/app.py`, `main.py` — bind `127.0.0.1` by default
- `web/backend/staker_backend/routes/*.py` — auth decorators on destructive endpoints
- `web/backend/staker_backend/config.py` — `STAKER_AUTH_TOKEN` config
- `tests/test_p0b_auth.py` — **NEW**: 36 tests (HTTP auth, Socket.IO auth, open read endpoints)

### P1a: ETH_DOCKER_PATH DI + EVM address validation (`594b9cd`)
- `core/paths.py` — **NEW**: centralized path resolver with env override
- `core/validation.py` — **NEW**: EVM address validator (regex + length + injection prevention)
- `commands/*.py`, `core/*.py` — replaced hardcoded `~/eth-docker` with DI
- `web/backend/staker_backend/schemas/*.py` — added address format validation
- `tests/test_p1a_validation.py` — **NEW**: 36 tests (address validation, path DI, schema checks)

### P1b: Error classification + JSON repair (`25797ac`)
- `web/backend/staker_backend/services/agent.py` — `classify_agent_error()`: buckets into context_overflow / rate_limit / timeout / other; `parse_tool_arguments()`: multi-level JSON repair (fence stripping, trailing commas, truncated bracket completion)
- Recovery paths: rate_limit/timeout retry stream creation with backoff; context_overflow compacts + trims history then retries once
- `tests/test_p1b_agent_error_repair.py` — **NEW**: 12 tests

### P2: Tool guardrail + smart compression + grace call (`99fa449`)
- `web/backend/staker_backend/services/agent.py` — circuit breaker (3 consecutive failures → block tool); `_summarize_tool_result()` preserves key diagnostic fields; grace call warns LLM at MAX_TURNS-2, omits tools on final turn
- `tests/test_p2_guardrail_grace.py` — **NEW**: 9 tests

### Operational fixes (`038cb9f`)
- `cli.py` + `commands/deploy.py` — `--dry-run` flag for demo mode
- `core/config/generator.py` — `STAKER_AGENT_CHECKPOINT_SYNC_URL` env override
- `core/node/status.py` — `docker compose ps -a` (show stopped containers)
- `web/backend/requirements.txt` — `python-telegram-bot[job-queue]`

## Verification

Reviewers can verify the scope using:

```bash
# All commits made during the hackathon
git log --after="2026-04-24" --before="2026-05-07" --pretty=format:"%h %ai %s"

# Diff stats for hackathon work
git diff --shortstat aed629f..HEAD

# Full diff
git diff aed629f..HEAD
```

## AI tool usage disclosure

Per ETHGlobal's AI usage rules:

- **AI assistants used**: Claude Code (Anthropic Claude Opus)
- **Where used**: security hardening implementation (P0a/P0b/P1a), agent resilience code (P1b/P2), test generation, documentation, code review
- **Where NOT used**: original architecture design (dual-loop agent, tool registry, monitor loop, memory system — all pre-hackathon), deployment orchestration logic, Ethereum-specific domain decisions (client selection, key generation, Lido CSM integration)
