# Remote Deployment Architecture Plan

## Objectives
- Enable Phase 0 requirement: one-command remote deployment of a single validator stack.
- Reuse existing CLI/back-end entry points while extending them to operate on remote Linux hosts.
- Leverage Ansible for idempotent provisioning (Docker, docker-compose, directory layout) and for distributing generated eth-docker configuration and compose files.
- Preserve the new job/Socket.IO infrastructure for streaming progress updates from long-running tasks.

## Core Flow
1. **Target Selection** – CLI flag (`--host user@ip`) or backend payload provides connection info; lookup defaults from `~/.staker-agent/hosts.yml`.
2. **Credential Resolution** – Support passwordless SSH keys by default; fall back to prompting once per session. Store runtime credentials in memory only.
3. **Preflight Checks** – Run a lightweight SSH probe that gathers OS details, CPU/RAM/disk, free ports, Docker presence, and available storage in `/var/lib/docker`. Implemented via a new `core/remote/preflight.py`.
4. **Workspace Sync** – Render `.env`, `docker-compose.yml`, monitoring configs locally (existing `ConfigGenerator`) then push to a temp directory on the host (`/opt/staker-agent/<network>`).
5. **Provisioning** – Execute Ansible playbooks:
   - `ansible/inventory/hosts.ini`
   - `ansible/playbooks/setup.yml` (install Docker, docker-compose, system packages)
   - `ansible/playbooks/deploy.yml` (create directories, copy rendered files, run `docker compose up -d`)
   - Roles split into `roles/common`, `roles/docker`, `roles/eth_docker`, `roles/monitoring`.
6. **Post-deploy Validation** – Run `docker ps`, tail logs, query validator and beacon health endpoints; feed results back to CLI/REST response.
7. **Monitoring Bootstrapping** – Ensure Prometheus/Grafana containers start with canned dashboards copied from `packs/monitoring/`.

## CLI Changes
- Extend `commands/deploy.run_deploy` to accept connection options and delegate to `RemoteDeployManager` when `--host` provided.
- Add `commands/init` step `--host` to remotely run environment checks only (no deployment).
- Introduce `core/remote/ssh_client.py` (wrapper over `paramiko` or `asyncssh`) and `core/remote/ansible_runner.py` to execute playbooks.
- Provide user-friendly progress logs mirroring local deployment (rich progress or streaming text).

## Backend Changes
- New `RemoteDeploymentService` in `staker_backend/services/remote.py` orchestrating preflight, config render, ansible run.
- Expose `/api/deploy/start` to accept `host`, `username`, `port`, `ssh_key`, `become` flags; queue jobs via job manager.
- Broadcast structured steps over WebSocket: `preflight`, `upload`, `ansible_setup`, `ansible_deploy`, `verify`.
- Persist remote host entries in `config/remote_hosts.yml` (read-only defaults) and allow overrides under `~/.staker-agent/hosts.yml`.

## Data Layout
```
ansible/
  inventory/
    hosts.ini         # generated per run
  playbooks/
    setup.yml
    deploy.yml
  roles/
    common/
    docker/
    eth_docker/
    monitoring/
core/remote/
  ssh_client.py
  ansible_runner.py
  preflight.py
  deploy_manager.py
```

Rendered config artifacts stored under `~/.staker-agent/artifacts/<host>/<timestamp>/`.

## Telemetry & Logging
- Capture Ansible stdout/stderr into per-job logs; stream trimmed updates via Socket.IO.
- Store raw logs under `~/.staker-agent/logs/<job-id>.log` for troubleshooting.
- Integrate job ID with CLI output to correlate CLI and backend runs.

## Testing Strategy
- Unit-test SSH helpers with paramiko stubs.
- Mock Ansible runner to confirm playbook invocations and error handling.
- Add integration test using a local Docker-in-Docker container to simulate remote host (longer-term).

## Next Steps
1. Scaffold `core/remote` module with SSH and preflight utilities.
2. Add Ansible playbooks/roles with minimal tasks (install Docker, create directories, copy files, launch compose).
3. Update CLI and backend to route deployment to remote manager when `host` provided.
4. Implement monitoring stack tasks in playbooks and validate Prometheus/Grafana containers start successfully.
5. Backfill documentation in `docs/REMOTE_DEPLOYMENT_GUIDE.md` once implementation is in place.
