"""Shared constants for the staker-agent backend."""
from __future__ import annotations

# Supported Ethereum networks
VALID_NETWORKS = ["mainnet", "hoodi", "holesky", "sepolia"]

# Networks that support Lido CSM
LIDO_CSM_NETWORKS = ["mainnet", "hoodi", "holesky"]

# Supported consensus-layer clients
VALID_CLIENTS = ["lighthouse", "prysm", "teku", "nimbus"]

# Lido CSM addresses — single source of truth.
# These are used for key generation AND info endpoints.
LIDO_CSM_ADDRESSES = {
    "mainnet": {
        "withdrawal_vault": "0xb9d7934878b5fb9610b3fe8a5e441e8fad7e293f",
        "el_rewards_vault": "0x388C818CA8B9251b393131C08a736A67ccB19297",
        "widget_url": "https://csm.lido.fi",
        "bond_amount": "2.4 ETH (or 1.5 ETH for early adopters)",
        "accepted_tokens": ["ETH", "stETH", "wstETH"],
    },
    "hoodi": {
        "withdrawal_vault": "0x4473dCDDbf77679A643BdB654dbd86D67F8d32f2",
        "el_rewards_vault": "0x9b108015fe433F173696Af3Aa0CF7CDb3E104258",
        "widget_url": "https://csm-holesky.lido.fi",
        "bond_amount": "0.1 ETH",
        "accepted_tokens": ["HETH"],
    },
    "holesky": {
        "withdrawal_vault": "0xF0179dEC45a37423EAD4FaD5fCb136197872EAd9",
        "el_rewards_vault": "0xE73a3602b99f1f913e72F8bdcBC235e206794Ac8",
        "widget_url": "https://csm-holesky.lido.fi",
        "bond_amount": "0.1 ETH",
        "accepted_tokens": ["ETH"],
    },
}
