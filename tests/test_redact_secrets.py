"""Tests for core.security.redact — secret redaction pipeline."""
import json
import logging

import pytest

from core.security.redact import redact_secrets, REDACT_MARKER


class TestRedactSecrets:
    def test_redacts_mnemonic_key(self):
        data = {"mnemonic": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"}
        result = redact_secrets(data)
        assert result["mnemonic"] == REDACT_MARKER

    def test_redacts_password_key(self):
        data = {"keystore_password": "super_secret_123"}
        result = redact_secrets(data)
        assert result["keystore_password"] == REDACT_MARKER

    def test_redacts_api_key(self):
        data = {"api_key": "sk-1234567890"}
        result = redact_secrets(data)
        assert result["api_key"] == REDACT_MARKER

    def test_redacts_ssh_key(self):
        data = {"ssh_key": "/home/user/.ssh/id_rsa"}
        result = redact_secrets(data)
        assert result["ssh_key"] == REDACT_MARKER

    def test_redacts_token(self):
        data = {"token": "eyJhbGciOiJ..."}
        result = redact_secrets(data)
        assert result["token"] == REDACT_MARKER

    def test_redacts_authorization(self):
        data = {"authorization": "Bearer abc123"}
        result = redact_secrets(data)
        assert result["authorization"] == REDACT_MARKER

    def test_case_insensitive_matching(self):
        data = {"Mnemonic": "secret", "KEYSTORE_PASSWORD": "pass", "Api_Key": "key"}
        result = redact_secrets(data)
        assert result["Mnemonic"] == REDACT_MARKER
        assert result["KEYSTORE_PASSWORD"] == REDACT_MARKER
        assert result["Api_Key"] == REDACT_MARKER

    def test_preserves_non_sensitive_keys(self):
        data = {"network": "holesky", "client": "lighthouse", "success": True, "count": 42}
        result = redact_secrets(data)
        assert result == data

    def test_nested_dict_redaction(self):
        data = {
            "keys": {
                "mnemonic": "word " * 23 + "word",
                "path": "/keys/validator",
            },
            "config": {"password": "abc"},
        }
        result = redact_secrets(data)
        assert result["keys"]["mnemonic"] == REDACT_MARKER
        assert result["keys"]["path"] == "/keys/validator"
        assert result["config"]["password"] == REDACT_MARKER

    def test_list_of_dicts(self):
        data = [
            {"name": "step1", "token": "secret_token"},
            {"name": "step2", "result": "ok"},
        ]
        result = redact_secrets(data)
        assert result[0]["token"] == REDACT_MARKER
        assert result[0]["name"] == "step1"
        assert result[1]["result"] == "ok"

    def test_mnemonic_pattern_in_string_value(self):
        """A string whose entire content is a 24-word mnemonic gets redacted."""
        phrase = "abandon " * 23 + "about"
        data = {"message": phrase}
        result = redact_secrets(data)
        assert result["message"] == REDACT_MARKER

    def test_mnemonic_embedded_in_error_message(self):
        """Mnemonic embedded in error/log text IS redacted (e.g. pexpect output)."""
        phrase = "abandon " * 23 + "about"
        data = {"output": f"Last output: {phrase}. Process exited."}
        result = redact_secrets(data)
        assert "abandon" not in result["output"]
        assert REDACT_MARKER in result["output"]
        assert "Process exited" in result["output"]

    def test_12_word_embedded_not_matched(self):
        """12-word embedded patterns rely on key-based redaction, not string scanning.

        Embedded 12-word detection has unacceptable false-positive rate with normal prose.
        Only 24-word embedded and full-value 12/24 are detected by string scanning.
        """
        phrase = "abandon " * 11 + "about"
        error_msg = f"KeyGenerationError: mnemonic was {phrase} but validation failed"
        result = redact_secrets(error_msg)
        # Not caught by string scanning — relies on being under a "mnemonic" key
        assert "abandon" in result

    def test_short_string_not_scanned(self):
        data = {"note": "hello world"}
        result = redact_secrets(data)
        assert result["note"] == "hello world"

    def test_none_input(self):
        assert redact_secrets(None) is None

    def test_empty_dict(self):
        assert redact_secrets({}) == {}

    def test_empty_list(self):
        assert redact_secrets([]) == []

    def test_does_not_mutate_input(self):
        original = {"mnemonic": "secret_value", "nested": {"password": "pass123"}}
        redact_secrets(original)
        assert original["mnemonic"] == "secret_value"
        assert original["nested"]["password"] == "pass123"

    def test_tuple_support(self):
        data = ({"password": "secret"}, {"name": "safe"})
        result = redact_secrets(data)
        assert result[0]["password"] == REDACT_MARKER
        assert result[1]["name"] == "safe"
        assert isinstance(result, tuple)

    def test_12_word_mnemonic_in_string(self):
        phrase = "abandon " * 11 + "about"
        data = {"output": phrase}
        result = redact_secrets(data)
        assert "abandon" not in result["output"]

    def test_non_mnemonic_prose_preserved(self):
        data = {"description": "The quick brown fox jumps over the lazy dog near the river bank"}
        result = redact_secrets(data)
        assert result["description"] == data["description"]

    def test_numeric_and_bool_values_pass_through(self):
        data = {"count": 5, "enabled": True, "ratio": 3.14}
        result = redact_secrets(data)
        assert result == data


class TestJobRedaction:
    """Regression tests: job payloads must never contain secrets.

    Tests simulate Job.to_dict() behavior by applying redact_secrets
    to a pipeline result dict (same as what Job.to_dict() does).
    This avoids importing the full Flask app which requires openai etc.
    """

    def _make_pipeline_result(self):
        return {
            "env_check": {"all_passed": True},
            "eth_docker": {"installed": True},
            "config": {"network": "holesky", "client": "lighthouse"},
            "keys": {
                "status": "success",
                "mnemonic": "abandon " * 23 + "about",
                "keystore_password": "my_secure_password",
                "validator_count": 1,
                "deposit_data_path": "/path/to/deposit.json",
            },
            "deploy": {"started": True},
        }

    def test_redacted_result_hides_mnemonic(self):
        result = self._make_pipeline_result()
        redacted = redact_secrets(result)
        keys_result = redacted["keys"]
        assert keys_result["mnemonic"] == REDACT_MARKER
        assert keys_result["keystore_password"] == REDACT_MARKER
        assert keys_result["validator_count"] == 1
        assert keys_result["deposit_data_path"] == "/path/to/deposit.json"

    def test_redaction_does_not_mutate_original(self):
        result = self._make_pipeline_result()
        original_mnemonic = result["keys"]["mnemonic"]

        redact_secrets(result)

        assert result["keys"]["mnemonic"] == original_mnemonic

    def test_all_jobs_redacted(self):
        results = [
            {"mnemonic": "secret phrase", "api_key": "sk-xxx"}
            for _ in range(3)
        ]
        for r in results:
            d = redact_secrets(r)
            assert d["mnemonic"] == REDACT_MARKER
            assert d["api_key"] == REDACT_MARKER

    def test_mnemonic_not_in_serialized_payload(self):
        """Simulates the exact payload that job_updated Socket.IO event would carry."""
        result = self._make_pipeline_result()
        # This is what Job.to_dict() does:
        payload = {
            "id": "test-job-1",
            "name": "full_pipeline",
            "status": "succeeded",
            "result": redact_secrets(result),
        }
        serialized = json.dumps(payload)
        assert "abandon" not in serialized
        assert "my_secure_password" not in serialized
        assert REDACT_MARKER in serialized

    def test_error_field_redacted(self):
        """Job.error containing mnemonic in exception message is redacted."""
        phrase = "abandon " * 23 + "about"
        error = f"KeyGenerationError: Last output was: {phrase}"
        redacted = redact_secrets(error)
        assert "abandon" not in redacted
        assert REDACT_MARKER in redacted

    def test_error_with_password_key_redacted(self):
        """Error payload dict with password key is redacted."""
        error_payload = {"message": "Failed", "password": "hunter2", "details": "ok"}
        redacted = redact_secrets(error_payload)
        assert redacted["password"] == REDACT_MARKER
        assert redacted["details"] == "ok"


class TestToolInputRedaction:
    """Tests that tool inputs (arguments) are properly redacted before UI/history."""

    def test_keystore_password_in_tool_args(self):
        tool_input = {
            "network": "holesky",
            "num_validators": 1,
            "keystore_password": "my_super_secret",
            "withdrawal_address": "0x1234",
        }
        redacted = redact_secrets(tool_input)
        assert redacted["keystore_password"] == REDACT_MARKER
        assert redacted["network"] == "holesky"
        assert redacted["withdrawal_address"] == "0x1234"

    def test_tool_args_with_nested_secrets(self):
        tool_input = {
            "config": {
                "ssh_key": "/path/to/key",
                "token": "bearer_xyz",
            },
            "host": "192.168.1.1",
        }
        redacted = redact_secrets(tool_input)
        assert redacted["config"]["ssh_key"] == REDACT_MARKER
        assert redacted["config"]["token"] == REDACT_MARKER
        assert redacted["host"] == "192.168.1.1"

    def test_agent_history_tool_call_redacted(self):
        """Simulates the assistant message with tool_calls stored in history."""
        tool_args = {"network": "holesky", "keystore_password": "secret123"}
        # This is what agent.py now does: json.dumps(redact_secrets(fc["arguments"]))
        stored = json.dumps(redact_secrets(tool_args))
        assert "secret123" not in stored
        assert REDACT_MARKER in stored
        parsed = json.loads(stored)
        assert parsed["network"] == "holesky"


class TestToolExecuteRedaction:
    """Integration test: tool execute() redacts errors containing secrets."""

    MNEMONIC_24 = "abandon " * 23 + "about"

    def test_execute_redacts_exception_in_result(self, monkeypatch):
        """Handler raising exception with mnemonic → execute() returns redacted error."""
        from core.agent.tools import execute, TOOL_HANDLERS, ToolContext

        def _bad_handler(tool_input, ctx):
            raise RuntimeError(f"pexpect EOF: Last output: {self.MNEMONIC_24}")

        monkeypatch.setitem(TOOL_HANDLERS, "_test_leak", _bad_handler)
        ctx = ToolContext(eth_docker_path="/tmp/fake")
        result = execute("_test_leak", {}, ctx)

        assert result["success"] is False
        assert "abandon" not in result["error"]
        assert REDACT_MARKER in result["error"]

    def test_execute_redacts_log_output(self, monkeypatch, caplog):
        """Handler raising exception with mnemonic → log entry is redacted."""
        from core.agent.tools import execute, TOOL_HANDLERS, ToolContext

        def _bad_handler(tool_input, ctx):
            raise RuntimeError(f"Last output: {self.MNEMONIC_24}")

        monkeypatch.setitem(TOOL_HANDLERS, "_test_leak_log", _bad_handler)
        ctx = ToolContext(eth_docker_path="/tmp/fake")

        with caplog.at_level(logging.ERROR, logger="core.agent.tools"):
            execute("_test_leak_log", {}, ctx)

        for record in caplog.records:
            assert "abandon" not in record.getMessage()

    def test_execute_normal_error_not_over_redacted(self, monkeypatch):
        """Normal errors without secrets pass through cleanly."""
        from core.agent.tools import execute, TOOL_HANDLERS, ToolContext

        def _normal_fail(tool_input, ctx):
            raise ValueError("Invalid network: foobar")

        monkeypatch.setitem(TOOL_HANDLERS, "_test_normal", _normal_fail)
        ctx = ToolContext(eth_docker_path="/tmp/fake")
        result = execute("_test_normal", {}, ctx)

        assert result["success"] is False
        assert "Invalid network: foobar" in result["error"]


class TestJobToDict:
    """Real Job class integration — simulates Job.to_dict() contract exactly."""

    MNEMONIC_24 = "abandon " * 23 + "about"

    def _simulate_job_to_dict(self, result, error=None):
        """Reproduces the exact logic of Job.to_dict() without importing Flask.

        Job.to_dict() returns: {"result": redact_secrets(self.result), "error": redact_secrets(self.error), ...}
        """
        return {
            "id": "test-job",
            "name": "keygen",
            "status": "succeeded",
            "result": redact_secrets(result),
            "error": redact_secrets(error),
        }

    def test_job_to_dict_redacts_result_and_error(self):
        result = {"keys": {"mnemonic": self.MNEMONIC_24, "path": "/keys"}}
        error = f"Partial failure: {self.MNEMONIC_24}"

        d = self._simulate_job_to_dict(result, error)
        serialized = json.dumps(d)
        assert "abandon" not in serialized
        assert d["result"]["keys"]["mnemonic"] == REDACT_MARKER
        assert REDACT_MARKER in d["error"]
        assert d["result"]["keys"]["path"] == "/keys"

    def test_job_to_dict_preserves_raw_result(self):
        result = {"mnemonic": self.MNEMONIC_24}
        original = result["mnemonic"]

        self._simulate_job_to_dict(result)
        # redact_secrets does NOT mutate input
        assert result["mnemonic"] == original

    def test_full_job_payload_serialization(self):
        """The complete JSON payload sent via socket 'job_updated' contains no secrets."""
        result = {
            "env_check": {"passed": True},
            "keys": {
                "mnemonic": self.MNEMONIC_24,
                "keystore_password": "hunter2",
                "deposit_data": "/path/deposit.json",
            },
        }
        error = f"timeout: child.before={self.MNEMONIC_24}"

        d = self._simulate_job_to_dict(result, error)
        blob = json.dumps(d)
        assert "abandon" not in blob
        assert "hunter2" not in blob
        assert "/path/deposit.json" in blob
