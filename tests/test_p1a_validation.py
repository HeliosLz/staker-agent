"""Tests for P1a: ETH_DOCKER_PATH DI + EVM address validation."""
from __future__ import annotations

import os
import sys

import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

WEB_BACKEND = os.path.join(BASE_DIR, "web", "backend")
if WEB_BACKEND not in sys.path:
    sys.path.insert(0, WEB_BACKEND)


# ---------------------------------------------------------------------------
# core/validation.py unit tests
# ---------------------------------------------------------------------------

class TestEVMAddressValidation:
    def test_valid_address_lowercase(self):
        from core.validation import is_valid_evm_address
        assert is_valid_evm_address("0x0000000000000000000000000000000000000000")

    def test_valid_address_mixed_case(self):
        from core.validation import is_valid_evm_address
        assert is_valid_evm_address("0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B")

    def test_invalid_too_short(self):
        from core.validation import is_valid_evm_address
        assert not is_valid_evm_address("0x1234")

    def test_invalid_too_long(self):
        from core.validation import is_valid_evm_address
        assert not is_valid_evm_address("0x" + "a" * 41)

    def test_invalid_no_prefix(self):
        from core.validation import is_valid_evm_address
        assert not is_valid_evm_address("ab5801a7d398351b8be11c439e05c5b3259aec9b")

    def test_invalid_non_hex(self):
        from core.validation import is_valid_evm_address
        assert not is_valid_evm_address("0xGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG")

    def test_none(self):
        from core.validation import is_valid_evm_address
        assert not is_valid_evm_address(None)

    def test_empty_string(self):
        from core.validation import is_valid_evm_address
        assert not is_valid_evm_address("")

    def test_newline_injection(self):
        """Address containing newline should NOT pass — prevents .env injection."""
        from core.validation import is_valid_evm_address
        assert not is_valid_evm_address("0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B\nMALICIOUS=true")

    def test_trailing_newline_rejected(self):
        """Trailing newline must be rejected (Python $ matches before \\n)."""
        from core.validation import is_valid_evm_address
        assert not is_valid_evm_address("0x" + "a" * 40 + "\n")

    def test_equals_injection(self):
        from core.validation import is_valid_evm_address
        assert not is_valid_evm_address("0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B=1")

    def test_validate_raises_on_invalid(self):
        from core.validation import validate_evm_address
        with pytest.raises(ValueError, match="fee_recipient"):
            validate_evm_address("not-an-address", "fee_recipient")

    def test_validate_returns_value(self):
        from core.validation import validate_evm_address
        addr = "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B"
        assert validate_evm_address(addr, "test") == addr


# ---------------------------------------------------------------------------
# ConfigGenerator validates addresses (defense in depth)
# ---------------------------------------------------------------------------

class TestConfigGeneratorValidation:
    def test_rejects_invalid_fee_recipient(self, tmp_path):
        from core.config.generator import ConfigGenerator
        gen = ConfigGenerator(str(tmp_path))
        with pytest.raises(ValueError, match="fee_recipient"):
            gen.generate_env(
                network="holesky",
                client="lighthouse",
                fee_recipient="INVALID",
            )

    def test_rejects_newline_in_withdrawal_address(self, tmp_path):
        from core.config.generator import ConfigGenerator
        gen = ConfigGenerator(str(tmp_path))
        with pytest.raises(ValueError, match="withdrawal_address"):
            gen.generate_env(
                network="holesky",
                client="lighthouse",
                withdrawal_address="0xAbc\nEVIL=1",
            )

    def test_accepts_valid_addresses(self, tmp_path):
        from core.config.generator import ConfigGenerator
        gen = ConfigGenerator(str(tmp_path))
        result = gen.generate_env(
            network="holesky",
            client="lighthouse",
            fee_recipient="0x0000000000000000000000000000000000000000",
            withdrawal_address="0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B",
        )
        assert result is True
        env_content = (tmp_path / ".env").read_text()
        assert "FEE_RECIPIENT=0x0000000000000000000000000000000000000000" in env_content
        assert "WITHDRAWAL_ADDRESS=0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B" in env_content


# ---------------------------------------------------------------------------
# ETH_DOCKER_PATH DI — no hardcoded ~/eth-docker fallbacks in core/
# ---------------------------------------------------------------------------

class TestEthDockerPathDI:
    def test_config_generator_requires_path(self):
        """ConfigGenerator no longer has a ~/eth-docker default."""
        from core.config.generator import ConfigGenerator
        import inspect
        sig = inspect.signature(ConfigGenerator.__init__)
        param = sig.parameters["eth_docker_path"]
        assert param.default is inspect.Parameter.empty

    def test_eth_docker_manager_requires_path(self):
        from core.docker.eth_docker import EthDockerManager
        import inspect
        sig = inspect.signature(EthDockerManager.__init__)
        param = sig.parameters["install_path"]
        assert param.default is inspect.Parameter.empty

    def test_key_manager_requires_path(self):
        from core.keys.manager import KeyManager
        import inspect
        sig = inspect.signature(KeyManager.__init__)
        param = sig.parameters["eth_docker_path"]
        assert param.default is inspect.Parameter.empty

    def test_deploy_manager_requires_path(self):
        from core.deploy.manager import DeployManager
        import inspect
        sig = inspect.signature(DeployManager.__init__)
        param = sig.parameters["eth_docker_path"]
        assert param.default is inspect.Parameter.empty

    def test_status_monitor_requires_path(self):
        from core.node.status import StatusMonitor
        import inspect
        sig = inspect.signature(StatusMonitor.__init__)
        param = sig.parameters["eth_docker_path"]
        assert param.default is inspect.Parameter.empty

    def test_config_validator_requires_path(self):
        from core.config.validator import ConfigValidator
        import inspect
        sig = inspect.signature(ConfigValidator.__init__)
        param = sig.parameters["eth_docker_path"]
        assert param.default is inspect.Parameter.empty


# ---------------------------------------------------------------------------
# Schema-level validation (marshmallow)
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    def test_config_schema_rejects_bad_fee_recipient(self):
        from staker_backend.schemas.configuration import ConfigRequestSchema
        from marshmallow import ValidationError
        schema = ConfigRequestSchema()
        with pytest.raises(ValidationError) as exc_info:
            schema.load({
                "network": "holesky",
                "client": "lighthouse",
                "fee_recipient": "not-valid",
            })
        assert "fee_recipient" in exc_info.value.messages

    def test_config_schema_rejects_bad_withdrawal_address(self):
        from staker_backend.schemas.configuration import ConfigRequestSchema
        from marshmallow import ValidationError
        schema = ConfigRequestSchema()
        with pytest.raises(ValidationError) as exc_info:
            schema.load({
                "network": "holesky",
                "client": "lighthouse",
                "withdrawal_address": "0xshort",
            })
        assert "withdrawal_address" in exc_info.value.messages

    def test_config_schema_accepts_valid(self):
        from staker_backend.schemas.configuration import ConfigRequestSchema
        schema = ConfigRequestSchema()
        data = schema.load({
            "network": "holesky",
            "client": "lighthouse",
            "fee_recipient": "0x0000000000000000000000000000000000000000",
        })
        assert data["fee_recipient"] == "0x0000000000000000000000000000000000000000"

    def test_pipeline_schema_rejects_bad_address(self):
        from staker_backend.schemas.pipeline import FullDeploySchema
        from marshmallow import ValidationError
        schema = FullDeploySchema()
        with pytest.raises(ValidationError) as exc_info:
            schema.load({
                "network": "holesky",
                "client": "lighthouse",
                "fee_recipient": "0xINJECT\nEVIL=1",
            })
        assert "fee_recipient" in exc_info.value.messages

    def test_pipeline_schema_allows_none_addresses(self):
        from staker_backend.schemas.pipeline import FullDeploySchema
        schema = FullDeploySchema()
        data = schema.load({
            "network": "holesky",
            "client": "lighthouse",
        })
        assert data["fee_recipient"] is None
        assert data["withdrawal_address"] is None

    def test_remote_deploy_schema_rejects_bad_fee_recipient(self):
        from staker_backend.schemas.remote import RemoteDeploySchema
        from marshmallow import ValidationError
        schema = RemoteDeploySchema()
        with pytest.raises(ValidationError) as exc_info:
            schema.load({
                "connection": {"host": "192.168.1.1"},
                "deployment": {
                    "network": "holesky",
                    "client": "lighthouse",
                    "fee_recipient": "INJECTED\nEVIL=1",
                },
            })
        assert "fee_recipient" in exc_info.value.messages.get("deployment", {})

    def test_remote_deploy_schema_rejects_bad_withdrawal(self):
        from staker_backend.schemas.remote import RemoteDeploySchema
        from marshmallow import ValidationError
        schema = RemoteDeploySchema()
        with pytest.raises(ValidationError) as exc_info:
            schema.load({
                "connection": {"host": "192.168.1.1"},
                "deployment": {
                    "network": "holesky",
                    "client": "lighthouse",
                    "withdrawal_address": "0xshort",
                },
            })
        assert "withdrawal_address" in exc_info.value.messages.get("deployment", {})

    def test_remote_deploy_schema_accepts_valid(self):
        from staker_backend.schemas.remote import RemoteDeploySchema
        schema = RemoteDeploySchema()
        data = schema.load({
            "connection": {"host": "192.168.1.1"},
            "deployment": {
                "network": "holesky",
                "client": "lighthouse",
                "fee_recipient": "0x0000000000000000000000000000000000000000",
            },
        })
        assert data["deployment"]["fee_recipient"] == "0x0000000000000000000000000000000000000000"


# ---------------------------------------------------------------------------
# core/paths.py centralized resolver
# ---------------------------------------------------------------------------

class TestPathResolver:
    def test_default_path(self, monkeypatch):
        monkeypatch.delenv("STAKER_AGENT_ETH_DOCKER_PATH", raising=False)
        from core.paths import get_eth_docker_path
        import importlib, core.paths
        importlib.reload(core.paths)
        from core.paths import get_eth_docker_path
        result = get_eth_docker_path()
        assert result.endswith("/eth-docker")
        assert "~" not in result

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("STAKER_AGENT_ETH_DOCKER_PATH", "/custom/path")
        from core.paths import get_eth_docker_path
        assert get_eth_docker_path() == "/custom/path"

    def test_relative_path_becomes_absolute(self, monkeypatch):
        """Relative env value must be resolved to absolute."""
        monkeypatch.setenv("STAKER_AGENT_ETH_DOCKER_PATH", "relative/eth-docker")
        from core.paths import get_eth_docker_path
        result = get_eth_docker_path()
        assert os.path.isabs(result)
        assert result.endswith("relative/eth-docker")

    def test_no_hardcoded_expanduser_in_cli(self):
        """Regression: no CLI file should contain expanduser('~/eth-docker')."""
        import glob
        cli_files = glob.glob(os.path.join(BASE_DIR, "commands", "*.py"))
        cli_files.append(os.path.join(BASE_DIR, "cli.py"))
        for path in cli_files:
            with open(path) as f:
                content = f.read()
            assert "expanduser" not in content, f"{path} still uses expanduser"

    def test_no_hardcoded_eth_docker_in_user_text(self):
        """Regression: user-facing text should not hardcode ~/eth-docker."""
        import glob
        cli_files = glob.glob(os.path.join(BASE_DIR, "commands", "*.py"))
        for path in cli_files:
            with open(path) as f:
                content = f.read()
            assert "~/eth-docker" not in content, f"{path} still has hardcoded ~/eth-docker text"


# ---------------------------------------------------------------------------
# websocket/logs.py stream_logs thread safety
# ---------------------------------------------------------------------------

class TestStreamLogsThreadSafety:
    def test_stream_logs_accepts_eth_docker_path_param(self):
        """stream_logs must accept eth_docker_path as a parameter (no current_app in thread)."""
        import inspect
        from websocket.logs import stream_logs
        sig = inspect.signature(stream_logs)
        assert "eth_docker_path" in sig.parameters

    def test_stream_logs_no_current_app_import(self):
        """stream_logs body must not reference current_app (runs outside app context)."""
        import inspect
        from websocket.logs import stream_logs
        source = inspect.getsource(stream_logs)
        assert "current_app" not in source
