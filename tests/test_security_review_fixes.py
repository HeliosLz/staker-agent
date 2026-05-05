"""Regression tests for security review fixes (P0a-P2 review findings)."""
from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web", "backend"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

CORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)


TEST_TOKEN = "test-secret-token-abc123"


def _make_fake_services():
    fake = MagicMock()
    fake.status.get_status.return_value = {"running": True}
    fake.status.fetch_logs.return_value = {"service": "consensus", "logs": "normal log line"}
    fake.status.start.return_value = None
    fake.status.stop.return_value = None
    fake.status.restart.return_value = None
    fake.deployment.generate_keys.return_value = {"status": "success", "mnemonic": "word1 word2"}
    fake.deployment.start.return_value = {"started": True}
    fake.deployment.import_keys.return_value = True
    fake.deployment.get_deposit_data.return_value = {}
    fake.deployment.get_lido_csm_info.return_value = {}
    fake.configuration.generate.return_value = {"network": "holesky"}
    fake.configuration.list_networks.return_value = ["mainnet", "holesky"]
    fake.configuration.list_clients.return_value = ["lighthouse"]
    fake.remote.preflight.return_value = {"success": True}
    mock_job = MagicMock()
    mock_job.id = "fake-job-id"
    mock_job.to_dict.return_value = {"id": "fake-job-id", "status": "running"}
    fake.jobs.submit.return_value = mock_job
    fake.agent_state = None
    fake.monitor_loop = None
    return fake


def _install_fake(app):
    fake = _make_fake_services()
    svc = app.extensions["services"]
    for attr in ("status", "deployment", "configuration", "remote", "jobs",
                 "agent_state", "monitor_loop"):
        setattr(svc, attr, getattr(fake, attr))
    return fake


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("STAKER_AGENT_API_TOKEN", TEST_TOKEN)
    from staker_backend import create_app
    application = create_app({"TESTING": True})
    _install_fake(application)
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers():
    return {"Authorization": f"Bearer {TEST_TOKEN}"}


# ---------------------------------------------------------------------------
# Issue 1: GET /api/auth/check — token validation endpoint
# ---------------------------------------------------------------------------

class TestAuthCheckEndpoint:
    def test_valid_token_returns_200(self, client, auth_headers):
        resp = client.get("/api/auth/check", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_wrong_token_returns_401(self, client):
        resp = client.get("/api/auth/check",
                          headers={"Authorization": "Bearer wrong-token"})
        assert resp.status_code == 401

    def test_missing_token_returns_401(self, client):
        resp = client.get("/api/auth/check")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Issue 2: POST /api/deploy/keys/generate requires X-Socket-ID
# ---------------------------------------------------------------------------

class TestKeygenRequiresSocketID:
    def test_keygen_without_socket_id_returns_422(self, client, auth_headers):
        resp = client.post("/api/deploy/keys/generate", headers=auth_headers,
                           json={"network": "holesky", "num_validators": 1})
        assert resp.status_code == 422
        data = resp.get_json()
        assert "X-Socket-ID" in data["message"]

    def test_keygen_with_socket_id_header_succeeds(self, client, auth_headers):
        headers = {**auth_headers, "X-Socket-ID": "fake-sid-123"}
        resp = client.post("/api/deploy/keys/generate", headers=headers,
                           json={"network": "holesky", "num_validators": 1})
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_keygen_without_auth_returns_401(self, client):
        resp = client.post("/api/deploy/keys/generate",
                           json={"network": "holesky", "num_validators": 1})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Issue 3: withdrawal_address validation in KeyGenerationSchema
# ---------------------------------------------------------------------------

class TestWithdrawalAddressValidation:
    def test_bad_address_returns_422(self, client, auth_headers):
        headers = {**auth_headers, "X-Socket-ID": "sid"}
        resp = client.post("/api/deploy/keys/generate", headers=headers,
                           json={"network": "holesky",
                                 "withdrawal_address": "not-an-address"})
        assert resp.status_code == 422
        data = resp.get_json()
        assert "withdrawal_address" in str(data.get("details", ""))

    def test_short_hex_returns_422(self, client, auth_headers):
        headers = {**auth_headers, "X-Socket-ID": "sid"}
        resp = client.post("/api/deploy/keys/generate", headers=headers,
                           json={"network": "holesky",
                                 "withdrawal_address": "0x1234"})
        assert resp.status_code == 422

    def test_valid_address_accepted(self, client, auth_headers):
        headers = {**auth_headers, "X-Socket-ID": "sid"}
        addr = "0x" + "a1" * 20
        resp = client.post("/api/deploy/keys/generate", headers=headers,
                           json={"network": "holesky",
                                 "withdrawal_address": addr})
        assert resp.status_code == 200

    def test_null_address_accepted(self, client, auth_headers):
        headers = {**auth_headers, "X-Socket-ID": "sid"}
        resp = client.post("/api/deploy/keys/generate", headers=headers,
                           json={"network": "holesky",
                                 "withdrawal_address": None})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Issue 4: /api/status/logs requires auth and redacts output
# ---------------------------------------------------------------------------

class TestLogsEndpointAuth:
    def test_logs_without_auth_returns_401(self, client):
        resp = client.get("/api/status/logs")
        assert resp.status_code == 401

    def test_logs_with_auth_returns_200(self, client, auth_headers):
        resp = client.get("/api/status/logs", headers=auth_headers)
        assert resp.status_code == 200

    def test_logs_redacts_secrets(self, client, auth_headers, app):
        svc = app.extensions["services"]
        svc.status.fetch_logs.return_value = {
            "service": "consensus",
            "logs": "line with secret STAKER_AGENT_API_TOKEN=mysecretvalue and more",
        }
        resp = client.get("/api/status/logs", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "mysecretvalue" not in data.get("logs", "")


# ---------------------------------------------------------------------------
# CORS: X-Socket-ID allowed in preflight
# ---------------------------------------------------------------------------

class TestCORSHeaders:
    def test_preflight_allows_x_socket_id(self, client):
        resp = client.options(
            "/api/deploy/keys/generate",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization,X-Socket-ID",
            },
        )
        allowed = resp.headers.get("Access-Control-Allow-Headers", "")
        assert "X-Socket-ID" in allowed


# ---------------------------------------------------------------------------
# redact_secrets: env-var KEY=VALUE pattern in strings
# ---------------------------------------------------------------------------

class TestEnvVarRedaction:
    def test_token_assignment_redacted(self):
        from core.security import redact_secrets
        text = "some log TOKEN=super-secret-123 more text"
        result = redact_secrets(text)
        assert "super-secret-123" not in result

    def test_password_assignment_redacted(self):
        from core.security import redact_secrets
        result = redact_secrets("config PASSWORD=hunter2 end")
        assert "hunter2" not in result

    def test_normal_text_preserved(self):
        from core.security import redact_secrets
        text = "container started successfully on port 8080"
        assert redact_secrets(text) == text

    def test_authorization_equals_bearer_redacted(self):
        from core.security import redact_secrets
        result = redact_secrets("Authorization=Bearer super-secret-token")
        assert "super-secret-token" not in result

    def test_authorization_colon_bearer_redacted(self):
        from core.security import redact_secrets
        result = redact_secrets("Authorization: Bearer super-secret-token")
        assert "super-secret-token" not in result

    def test_authorization_bearer_case_insensitive(self):
        from core.security import redact_secrets
        result = redact_secrets("authorization: bearer my-token-123 end")
        assert "my-token-123" not in result


# ---------------------------------------------------------------------------
# P3: WebSocket subprocess leak — _kill_stream cleans up tracked processes
# ---------------------------------------------------------------------------

class TestWebSocketStreamCleanup:
    def test_kill_stream_terminates_tracked_process(self):
        import threading
        from unittest.mock import MagicMock
        from web.backend.websocket.logs import _active_streams, _kill_stream, _streams_lock

        fake_proc = MagicMock()
        fake_proc.poll.return_value = None  # still running
        stop_event = threading.Event()

        with _streams_lock:
            _active_streams["test-sid"] = (fake_proc, stop_event)

        _kill_stream("test-sid")

        assert stop_event.is_set()
        fake_proc.kill.assert_called_once()
        fake_proc.wait.assert_called_once()
        assert "test-sid" not in _active_streams

    def test_kill_stream_noop_for_unknown_sid(self):
        from web.backend.websocket.logs import _kill_stream, _active_streams
        _kill_stream("nonexistent-sid")
        assert "nonexistent-sid" not in _active_streams

    def test_kill_stream_skips_already_exited(self):
        import threading
        from unittest.mock import MagicMock
        from web.backend.websocket.logs import _active_streams, _kill_stream, _streams_lock

        fake_proc = MagicMock()
        fake_proc.poll.return_value = 0  # already exited
        stop_event = threading.Event()

        with _streams_lock:
            _active_streams["done-sid"] = (fake_proc, stop_event)

        _kill_stream("done-sid")

        assert stop_event.is_set()
        fake_proc.kill.assert_not_called()
        assert "done-sid" not in _active_streams

    def test_subscribe_kills_previous_stream(self):
        """Re-subscribing should kill the old stream before starting a new one."""
        import threading
        from unittest.mock import MagicMock
        from web.backend.websocket.logs import _active_streams, _kill_stream, _streams_lock

        old_proc = MagicMock()
        old_proc.poll.return_value = None
        stop_event = threading.Event()
        with _streams_lock:
            _active_streams["resub-sid"] = (old_proc, stop_event)

        _kill_stream("resub-sid")
        assert stop_event.is_set()
        old_proc.kill.assert_called_once()
        assert "resub-sid" not in _active_streams

    def test_race_disconnect_before_popen_registered(self):
        """If disconnect fires between thread start and Popen registration,
        stop_event prevents orphan."""
        import threading
        from web.backend.websocket.logs import _active_streams, _kill_stream, _streams_lock

        stop_event = threading.Event()
        with _streams_lock:
            _active_streams["race-sid"] = (None, stop_event)

        # Simulate disconnect arriving before Popen is stored
        _kill_stream("race-sid")

        assert stop_event.is_set()
        assert "race-sid" not in _active_streams

    def test_stream_logs_aborts_when_stop_event_preset(self):
        """stream_logs returns immediately if stop_event is already set."""
        import threading
        from unittest.mock import MagicMock, patch
        from web.backend.websocket.logs import stream_logs

        stop_event = threading.Event()
        stop_event.set()
        mock_socketio = MagicMock()

        with patch("web.backend.websocket.logs.subprocess") as mock_sub:
            stream_logs(mock_socketio, "abort-sid", "consensus", "logs_consensus",
                        "/tmp", stop_event)
            mock_sub.Popen.assert_not_called()

    def test_stale_finalizer_does_not_clobber_new_stream(self):
        """Old stream's finally must not remove a newer stream's entry."""
        import threading
        from unittest.mock import MagicMock
        from web.backend.websocket.logs import _active_streams, _streams_lock

        sid = "overlap-sid"
        old_event = threading.Event()
        new_event = threading.Event()
        new_proc = MagicMock()
        new_proc.poll.return_value = None

        # Simulate: new stream already registered while old is in finally
        with _streams_lock:
            _active_streams[sid] = (new_proc, new_event)

        # Old finalizer tries to clean up — should NOT delete because event differs
        with _streams_lock:
            entry = _active_streams.get(sid)
            if entry is not None and entry[1] is old_event:
                del _active_streams[sid]

        # New stream entry must survive
        assert sid in _active_streams
        assert _active_streams[sid][1] is new_event

        # Cleanup
        with _streams_lock:
            _active_streams.pop(sid, None)
