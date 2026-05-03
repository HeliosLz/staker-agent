"""Tests for P0b: localhost binding + bearer auth."""
from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web", "backend"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_TOKEN = "test-secret-token-abc123"


class _FakeServices:
    """Stub ServiceContainer — no real Docker/config/key side effects."""
    def __init__(self):
        self.status = MagicMock()
        self.status.get_status.return_value = {"running": True}
        self.status.start.return_value = None
        self.status.stop.return_value = None
        self.status.restart.return_value = None
        self.status.fetch_logs.return_value = []

        self.deployment = MagicMock()
        self.deployment.start.return_value = {"started": True}
        self.deployment.generate_keys.return_value = {"status": "success"}
        self.deployment.import_keys.return_value = True
        self.deployment.get_deposit_data.return_value = {}
        self.deployment.get_lido_csm_info.return_value = {}

        self.configuration = MagicMock()
        self.configuration.generate.return_value = {"network": "holesky"}
        self.configuration.list_networks.return_value = ["mainnet", "holesky"]
        self.configuration.list_clients.return_value = ["lighthouse", "prysm"]

        self.remote = MagicMock()
        self.remote.preflight.return_value = {"success": True}

        self.jobs = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "fake-job-id"
        mock_job.to_dict.return_value = {"id": "fake-job-id", "status": "running"}
        self.jobs.submit.return_value = mock_job

        self.agent_state = None
        self.monitor_loop = None


def _install_fake_services(application):
    """Swap service attributes on the real ServiceContainer.

    get_services() requires app.extensions["services"] to remain a
    ServiceContainer, so replace only the side-effecting collaborators.
    """
    fake = _FakeServices()
    services = application.extensions["services"]
    services.status = fake.status
    services.deployment = fake.deployment
    services.configuration = fake.configuration
    services.remote = fake.remote
    services.jobs = fake.jobs
    services.agent_state = fake.agent_state
    services.monitor_loop = fake.monitor_loop
    return fake


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("STAKER_AGENT_API_TOKEN", TEST_TOKEN)
    from staker_backend import create_app
    application = create_app({"TESTING": True})
    _install_fake_services(application)
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers():
    return {"Authorization": f"Bearer {TEST_TOKEN}"}


# ---------------------------------------------------------------------------
# Default host binding — static regression
# ---------------------------------------------------------------------------

class TestDefaultHost:
    def test_default_host_constant_is_localhost(self):
        from staker_backend.auth import DEFAULT_HOST
        assert DEFAULT_HOST == "127.0.0.1"

    def test_main_py_uses_default_host(self):
        """Regression: main.py must reference DEFAULT_HOST, not hardcode 0.0.0.0."""
        main_path = os.path.join(BASE_DIR, "main.py")
        with open(main_path) as f:
            source = f.read()
        assert "DEFAULT_HOST" in source
        assert '"0.0.0.0"' not in source

    def test_app_py_uses_default_host(self):
        """Regression: app.py must reference DEFAULT_HOST, not hardcode 0.0.0.0."""
        app_path = os.path.join(BASE_DIR, "app.py")
        with open(app_path) as f:
            source = f.read()
        assert "DEFAULT_HOST" in source
        assert '"0.0.0.0"' not in source

    def test_env_override_still_works(self, monkeypatch):
        monkeypatch.setenv("STAKER_AGENT_HOST", "0.0.0.0")
        from staker_backend.auth import DEFAULT_HOST
        host = os.getenv("STAKER_AGENT_HOST", DEFAULT_HOST)
        assert host == "0.0.0.0"


# ---------------------------------------------------------------------------
# HTTP Bearer auth — success (stub services, no side effects)
# ---------------------------------------------------------------------------

class TestHTTPAuthSuccess:
    def test_status_start_with_valid_token(self, client, auth_headers):
        resp = client.post("/api/status/start", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_status_stop_with_valid_token(self, client, auth_headers):
        resp = client.post("/api/status/stop", headers=auth_headers)
        assert resp.status_code == 200

    def test_status_restart_with_valid_token(self, client, auth_headers):
        resp = client.post("/api/status/restart", headers=auth_headers)
        assert resp.status_code == 200

    def test_deploy_start_with_valid_token(self, client, auth_headers):
        resp = client.post("/api/deploy/start", headers=auth_headers, json={})
        # 202 Accepted (background job)
        assert resp.status_code == 202

    def test_config_generate_with_valid_token(self, client, auth_headers):
        resp = client.post("/api/config/generate", headers=auth_headers,
                          json={"network": "holesky", "client": "lighthouse"})
        assert resp.status_code == 200

    def test_agent_apikey_with_valid_token(self, client, auth_headers, monkeypatch):
        import staker_backend.routes.agent as agent_routes
        monkeypatch.setattr(agent_routes, "set_api_key", lambda _key: (True, ""))
        resp = client.post("/api/agent/apikey", headers=auth_headers,
                          json={"api_key": "sk-test"})
        assert resp.status_code == 200

    def test_remote_preflight_with_valid_token(self, client, auth_headers):
        resp = client.post("/api/remote/preflight", headers=auth_headers,
                          json={"host": "192.168.1.1"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# HTTP Bearer auth — missing token → 401
# ---------------------------------------------------------------------------

class TestHTTPAuthMissing:
    @pytest.mark.parametrize(
        "path",
        [
            "/api/status/start",
            "/api/status/stop",
            "/api/status/restart",
            "/api/deploy/full",
            "/api/deploy/start",
            "/api/deploy/keys/generate",
            "/api/deploy/keys/import",
            "/api/config/generate",
            "/api/remote/preflight",
            "/api/agent/apikey",
        ],
    )
    def test_protected_post_no_token(self, client, path):
        resp = client.post(path, json={})
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"] == "authentication_required"


# ---------------------------------------------------------------------------
# HTTP Bearer auth — wrong token → 401
# ---------------------------------------------------------------------------

class TestHTTPAuthWrongToken:
    def test_status_start_wrong_token(self, client):
        resp = client.post("/api/status/start",
                          headers={"Authorization": "Bearer wrong-token"})
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"] == "authentication_required"
        assert "Invalid" in data["message"]

    def test_deploy_full_wrong_token(self, client):
        resp = client.post("/api/deploy/full", json={},
                          headers={"Authorization": "Bearer nope"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# HTTP read-only GET endpoints remain open (no auth required)
# ---------------------------------------------------------------------------

class TestReadOnlyEndpointsOpen:
    def test_health_no_auth(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_status_get_no_auth(self, client):
        resp = client.get("/api/status/")
        assert resp.status_code == 200

    def test_config_networks_no_auth(self, client):
        resp = client.get("/api/config/networks")
        assert resp.status_code == 200

    def test_config_clients_no_auth(self, client):
        resp = client.get("/api/config/clients")
        assert resp.status_code == 200

    def test_agent_apikey_status_no_auth(self, client):
        resp = client.get("/api/agent/apikey/status")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Token not configured — 503
# ---------------------------------------------------------------------------

class TestTokenNotConfigured:
    @pytest.fixture()
    def notoken_client(self, monkeypatch):
        monkeypatch.delenv("STAKER_AGENT_API_TOKEN", raising=False)
        from staker_backend import create_app
        application = create_app({"TESTING": True})
        _install_fake_services(application)
        return application.test_client()

    def test_destructive_returns_503_when_no_token(self, notoken_client):
        resp = notoken_client.post("/api/status/start")
        assert resp.status_code == 503
        data = resp.get_json()
        assert data["error"] == "token_not_configured"

    def test_deploy_returns_503_when_no_token(self, notoken_client):
        resp = notoken_client.post("/api/deploy/start", json={})
        assert resp.status_code == 503

    def test_get_endpoints_unaffected_by_missing_token(self, notoken_client):
        resp = notoken_client.get("/api/health")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Socket.IO auth
# ---------------------------------------------------------------------------

class TestSocketIOAuth:
    @pytest.fixture()
    def sio_app(self, monkeypatch):
        monkeypatch.setenv("STAKER_AGENT_API_TOKEN", TEST_TOKEN)
        from staker_backend import create_app
        from staker_backend.extensions import socketio as sio
        from websocket import init_socketio

        application = create_app({"TESTING": True})
        _install_fake_services(application)

        init_socketio(sio)
        return application, sio

    def test_connect_with_raw_token(self, sio_app):
        app, sio = sio_app
        client = sio.test_client(app, auth={"token": TEST_TOKEN})
        assert client.is_connected()
        client.disconnect()

    def test_connect_with_bearer_prefix(self, sio_app):
        app, sio = sio_app
        client = sio.test_client(app, auth={"token": f"Bearer {TEST_TOKEN}"})
        assert client.is_connected()
        client.disconnect()

    def test_connect_without_token_rejected(self, sio_app):
        app, sio = sio_app
        client = sio.test_client(app)
        assert not client.is_connected()

    def test_connect_wrong_token_rejected(self, sio_app):
        app, sio = sio_app
        client = sio.test_client(app, auth={"token": "wrong"})
        assert not client.is_connected()

    def test_connect_no_token_configured_rejected(self, monkeypatch):
        monkeypatch.delenv("STAKER_AGENT_API_TOKEN", raising=False)
        from staker_backend import create_app
        from staker_backend.extensions import socketio as sio
        from websocket import init_socketio

        application = create_app({"TESTING": True})
        init_socketio(sio)
        client = sio.test_client(application, auth={"token": "anything"})
        assert not client.is_connected()
