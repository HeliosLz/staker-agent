"""Deployment orchestration services."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from core.deploy.manager import DeployManager
from core.keys.manager import KeyManager

VALID_NETWORKS = ["mainnet", "hoodi", "holesky", "sepolia"]
LIDO_CSM_NETWORKS = ["mainnet", "hoodi", "holesky"]

if TYPE_CHECKING:
    from ..repositories.filesystem import FileRepository


class DeploymentService:
    """Service facade around deployment workflows."""

    def __init__(self, eth_docker_path: str, files: "FileRepository") -> None:
        self.eth_docker_path = eth_docker_path
        self._files = files

    def start(self) -> bool:
        deployer = DeployManager()
        return bool(deployer.deploy())

    def generate_keys(self, *, network: str, num_validators: int, withdrawal_address: str | None, use_lido_csm: bool) -> Dict[str, Any]:
        if network not in VALID_NETWORKS:
            raise ValueError(f"Invalid network '{network}'. Must be one of: {', '.join(VALID_NETWORKS)}")
        if use_lido_csm and network not in LIDO_CSM_NETWORKS:
            raise ValueError("Lido CSM is only available on mainnet, hoodi, and holesky")

        key_manager = KeyManager()
        return key_manager.generate_keys(
            network=network,
            num_validators=num_validators,
            withdrawal_address=withdrawal_address,
            use_lido_csm=use_lido_csm,
        )

    def import_keys(self, keys_path: str) -> bool:
        key_manager = KeyManager()
        return bool(key_manager.import_keys(keys_path))

    def get_deposit_data(self) -> Dict[str, Any]:
        key_manager = KeyManager()
        deposit_data_path = key_manager._find_deposit_data()  # type: ignore[attr-defined]

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
        if network == "mainnet":
            return {
                "network": "mainnet",
                "widget_url": "https://csm.lido.fi",
                "withdrawal_vault": "0xb9d7934878b5fb9610b3fe8a5e441e8fad7e293f",
                "el_rewards_vault": "0x388C818CA8B9251b393131C08a736A67ccB19297",
                "bond_amount": "2.4 ETH (or 1.5 ETH for early adopters)",
                "accepted_tokens": ["ETH", "stETH", "wstETH"],
                "steps": [
                    "Generate validator keys with Lido CSM withdrawal address",
                    "Upload deposit_data.json to Lido CSM Widget",
                    "Submit bond (2.4 ETH or 1.5 ETH)",
                    "Await operator approval and validator activation",
                ],
            }

        if network == "hoodi":
            return {
                "network": "hoodi",
                "widget_url": "https://csm-holesky.lido.fi",
                "withdrawal_vault": "0x2C674ba3c21Ec154910A9a31b6E4093B88000Fb0",
                "el_rewards_vault": "0x7950C7588921F24452d7b9D3468A2DD043bFA033",
                "bond_amount": "0.1 ETH",
                "accepted_tokens": ["HETH"],
                "steps": [
                    "Generate validator keys for Hoodi network",
                    "Upload deposit_data.json to CSM widget",
                    "Stake required testnet bond",
                    "Activate validator once assigned",
                ],
            }

        if network == "holesky":
            return {
                "network": "holesky",
                "widget_url": "https://csm-holesky.lido.fi",
                "withdrawal_vault": "0x16cB98630f3350F7E28B910A27b879ac67e77374",
                "el_rewards_vault": "0x2Ce5ca9C5Dd263B67A6ffCbCe3A827108da73ab2",
                "bond_amount": "0.1 ETH",
                "accepted_tokens": ["ETH"],
                "steps": [
                    "Generate validator keys for Holesky network",
                    "Upload deposit_data.json to CSM widget",
                    "Stake bond in Holesky ETH",
                    "Confirm validator activation",
                ],
            }

        return {
            "network": network,
            "message": "Lido CSM information unavailable for this network.",
        }
