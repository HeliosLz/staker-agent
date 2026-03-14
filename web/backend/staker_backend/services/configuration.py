"""Configuration management service."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Dict, List

from core.config.generator import ConfigGenerator

VALID_NETWORKS = ["mainnet", "hoodi", "holesky", "sepolia"]
VALID_CLIENTS = ["lighthouse", "prysm", "teku", "nimbus"]

if TYPE_CHECKING:
    from ..repositories.filesystem import FileRepository


class ConfigurationError(RuntimeError):
    """Raised when configuration generation fails."""


class ConfigurationService:
    """Generate and describe eth-docker configuration."""

    def __init__(self, eth_docker_path: str, files: "FileRepository") -> None:
        self.eth_docker_path = eth_docker_path
        self._files = files

    def generate(self, *, network: str, client: str, fee_recipient: str | None, withdrawal_address: str | None) -> Dict[str, Any]:
        if network not in VALID_NETWORKS:
            raise ValueError(f"Invalid network '{network}'. Must be one of: {', '.join(VALID_NETWORKS)}")
        if client not in VALID_CLIENTS:
            raise ValueError(f"Invalid client '{client}'. Must be one of: {', '.join(VALID_CLIENTS)}")

        generator = ConfigGenerator()
        success = generator.generate_env(
            network=network,
            client=client,
            fee_recipient=fee_recipient,
            withdrawal_address=withdrawal_address,
        )

        if not success:
            raise ConfigurationError("Failed to generate configuration")

        config_path = os.path.join(generator.eth_docker_path, ".env")
        config_content = self._files.read_text(config_path)

        return {
            "network": network,
            "client": client,
            "config_path": config_path,
            "config_content": config_content,
        }

    @staticmethod
    def list_networks() -> List[Dict[str, Any]]:
        return [
            {
                "id": "mainnet",
                "name": "Mainnet",
                "description": "Ethereum Mainnet - Production network",
                "recommended": False,
            },
            {
                "id": "hoodi",
                "name": "Hoodi",
                "description": "Hoodi Testnet - Lido official test network",
                "recommended": True,
            },
            {
                "id": "holesky",
                "name": "Holesky",
                "description": "Holesky Testnet - General Ethereum testnet",
                "recommended": False,
            },
            {
                "id": "sepolia",
                "name": "Sepolia",
                "description": "Sepolia Testnet",
                "recommended": False,
            },
        ]

    @staticmethod
    def list_clients() -> List[Dict[str, Any]]:
        return [
            {
                "id": "lighthouse",
                "name": "Lighthouse",
                "language": "Rust",
                "description": "High performance, low resource usage",
                "recommended": True,
            },
            {
                "id": "prysm",
                "name": "Prysm",
                "language": "Go",
                "description": "Feature-rich and community driven",
                "recommended": False,
            },
            {
                "id": "teku",
                "name": "Teku",
                "language": "Java",
                "description": "Enterprise-grade stability",
                "recommended": False,
            },
            {
                "id": "nimbus",
                "name": "Nimbus",
                "language": "Nim",
                "description": "Lightweight option for constrained hardware",
                "recommended": False,
            },
        ]
