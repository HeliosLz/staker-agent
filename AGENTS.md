# Repository Guidelines

## Project Structure & Module Organization
`cli.py` is the entry point and routes to modular handlers in `commands/` (e.g., `commands/setup.py`, `commands/keys.py`). Deployment logic, configuration engines, and validator services live in `core/`. Defaults and rendered assets are in `config/`, `templates/`, and `packs/`, while automation helpers sit in `ansible/` and `scripts/` (notably `scripts/gcp-setup.sh`). The optional dashboard resides in `web/` with separate `frontend/` and `backend/`; the backend boots via `web/backend/app.py`, which delegates to the modular `staker_backend` package (app factory, repositories, services, job manager, and Socket.IO handlers). Add automated checks under `tests/`, collocating fixtures with the modules they cover.

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate` — create an isolated environment for development.
- `pip install -r requirements.txt` — install the CLI dependencies (`click`, `rich`, `pyyaml`, etc.).
- `python3 cli.py init` — run the environment diagnostics; use `--help` on any subcommand for options.
- `python3 cli.py configure --network holesky --client lighthouse` — quickest configuration flow for testnet work.
- `python3 cli.py deploy` — perform the full deployment workflow; pair with `python3 cli.py status` for health checks.
- `python3 -m pytest tests` — execute repository tests once they are added (see guidance below). Backend-specific dependencies live in `web/backend/requirements.txt`; install them in an isolated env when contributing to the web server (`pip install -r web/backend/requirements.txt`).

## Coding Style & Naming Conventions
Target Python 3.10+ with PEP 8 defaults: 4-space indentation, `snake_case` for modules/functions, and `PascalCase` for classes. Keep command names concise verbs (`init`, `deploy`, `status`). Structure CLI output with `rich` components to match the current UX, and keep YAML/templates at two-space indentation. Backend APIs should use the centralized error responses in `web/backend/staker_backend/errors.py`; raise `ApiError` derivatives instead of handcrafting JSON. Auto-format locally with `black` or `ruff` if helpful, but avoid committing tool caches.

## Testing Guidelines
Adopt `pytest` with files named `test_*.py` inside `tests/` mirroring the module under test (e.g., `tests/test_env_checker.py`). Mock Docker, network calls, and filesystem writes so suites stay offline. For the Flask backend, rely on the app factory to spin up test clients, stub repositories/job manager for async flows, and assert standardized error payloads. Cover happy-path and failure handling for each CLI command or core service, and add regression cases before closing bug fixes.

## Commit & Pull Request Guidelines
Follow the Conventional Commits style already in history (`feat:`, `fix:`, `chore:`) using imperative phrasing that states the behavior change. PRs should summarize the change, note the tests executed (`pytest`, backend job tests), link issues, and attach screenshots or logs for UX updates. Call out configuration or security-sensitive steps, list `.env` updates, and highlight API/WebSocket changes (e.g., `/api/jobs`, `job_updated` events) so the UI team can react promptly.

## Security & Configuration Tips
Never commit `.env` files, validator secrets, or keystores. Start from templates in `config/`, documenting overrides in `docs/` when they affect operators. Redact wallet addresses and API tokens from snippets, and review `core/security/` helpers before changing key-handling flows.

## Backend Refactor Roadmap
- Queue remote deployment jobs that orchestrate Ansible/SSH tasks and stream structured progress events to Socket.IO clients.
- Implement a validator key vault service with encrypted storage, backup/export endpoints, and end-to-end backend tests.
- Add monitoring endpoints that expose Prometheus/Grafana configuration, alert routing, and node health audits.
