"""Deployment orchestration services."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from core.deploy.manager import DeployManager
from core.keys.manager import KeyManager

from ..constants import VALID_NETWORKS, LIDO_CSM_NETWORKS, LIDO_CSM_ADDRESSES

if TYPE_CHECKING:
    from ..repositories.filesystem import FileRepository

_LIDO_CSM_STEPS = {
    "mainnet": [
        "Generate validator keys with Lido CSM withdrawal address",
        "Upload deposit_data.json to Lido CSM Widget",
        "Submit bond (2.4 ETH or 1.5 ETH)",
        "Await operator approval and validator activation",
    ],
    "hoodi": [
        "Generate validator keys for Hoodi network",
        "Upload deposit_data.json to CSM widget",
        "Stake required testnet bond",
        "Activate validator once assigned",
    ],
    "holesky": [
        "Generate validator keys for Holesky network",
        "Upload deposit_data.json to CSM widget",
        "Stake bond in Holesky ETH",
        "Confirm validator activation",
    ],
}


class DeploymentService:
    """Service facade around deployment workflows."""

    def __init__(self, eth_docker_path: str, files: "FileRepository") -> None:
        self.eth_docker_path = eth_docker_path
        self._files = files
        self._key_manager = KeyManager(eth_docker_path=eth_docker_path)

    def install_eth_docker(self) -> bool:
        """Install eth-docker using the existing install_path."""
        from core.docker.eth_docker import EthDockerManager
        manager = EthDockerManager(install_path=self.eth_docker_path)
        return manager.install()

    def start(self) -> bool:
        deployer = DeployManager()
        return bool(deployer.deploy())

    def generate_keys(self, *, network: str, num_validators: int, withdrawal_address: str | None, use_lido_csm: bool, keystore_password: str | None = None) -> Dict[str, Any]:
        if network not in VALID_NETWORKS:
            raise ValueError(f"Invalid network '{network}'. Must be one of: {', '.join(VALID_NETWORKS)}")
        if use_lido_csm and network not in LIDO_CSM_NETWORKS:
            raise ValueError("Lido CSM is only available on mainnet, hoodi, and holesky")

        return self._key_manager.generate_keys(
            network=network,
            num_validators=num_validators,
            withdrawal_address=withdrawal_address,
            use_lido_csm=use_lido_csm,
            keystore_password=keystore_password,
        )

    def import_keys(self, keys_path: str) -> bool:
        return bool(self._key_manager.import_keys(keys_path))

    def get_deposit_data(self) -> Dict[str, Any]:
        deposit_data_path = self._key_manager._find_deposit_data()  # type: ignore[attr-defined]

        if not deposit_data_path or not self._files.exists(deposit_data_path):
            raise FileNotFoundError("deposit_data.json not found. Generate keys first.")

        deposit_data = self._files.read_json(deposit_data_path)

        count = len(deposit_data) if isinstance(deposit_data, list) else 1
        return {
            "path": deposit_data_path,
            "content": deposit_data,
            "validator_count": count,
        }

    @staticmethod
    def get_lido_csm_info(network: str) -> Dict[str, Any]:
        addrs = LIDO_CSM_ADDRESSES.get(network)
        if not addrs:
            return {
                "network": network,
                "message": "Lido CSM information unavailable for this network.",
            }
        return {
            "network": network,
            "widget_url": addrs["widget_url"],
            "withdrawal_vault": addrs["withdrawal_vault"],
            "el_rewards_vault": addrs["el_rewards_vault"],
            "bond_amount": addrs["bond_amount"],
            "accepted_tokens": addrs["accepted_tokens"],
            "steps": _LIDO_CSM_STEPS.get(network, []),
        }
