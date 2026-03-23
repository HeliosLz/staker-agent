---
name: lido-csm
description: Lido CSM operation guide, bond requirements, withdrawal vault, strike policy
---

# Lido Community Staking Module (CSM)

## Overview
CSM allows solo stakers to run validators with less than 32 ETH by providing a bond (2.4 ETH on mainnet) and receiving staked ETH from Lido's pool.

## Registration Flow
1. Generate validator keys with CSM withdrawal vault address
2. Upload deposit_data.json to CSM Widget
3. Submit bond (ETH, stETH, or wstETH)
4. Wait for operator approval and validator activation

## Withdrawal Vault Addresses
- Mainnet: `0xb9d7934878b5fb9610b3fe8a5e441e8fad7e293f`
- Holesky: `0xF0179dEC45a37423EAD4FaD5fCb136197872EAd9`
- Hoodi: `0x4473dCDDbf77679A643BdB654dbd86D67F8d32f2`

**CRITICAL**: The withdrawal address must be set to the CSM withdrawal vault, NOT your personal address. This is set during key generation and cannot be changed.

## Bond Requirements
- Mainnet: 2.4 ETH (1.5 ETH for early adopters)
- Holesky/Hoodi testnet: 0.1 ETH

## Performance Requirements
- Validators must maintain acceptable attestation performance
- Excessive missed attestations lead to "strikes"
- Multiple strikes can result in forced exit and bond confiscation

## Strike Policy
- Strike issued after prolonged poor performance
- Recovery period between strikes
- Operators should monitor attestation effectiveness closely
- Target: >95% attestation rate

## Rewards
- Operator fee: percentage of validator rewards
- Bond earns staking rewards
- MEV rewards distributed according to protocol rules

## Key Differences from Solo Staking
- Lower capital requirement (2.4 ETH vs 32 ETH)
- Must use Lido's withdrawal vault address
- Subject to CSM performance requirements
- Bond can be partially confiscated for poor performance
