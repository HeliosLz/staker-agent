---
name: staking
description: Ethereum staking mechanics, slashing rules, attestation requirements
---

# Ethereum Staking Knowledge

## Validator Lifecycle
- Deposit 32 ETH to the deposit contract
- Wait for entry queue (can take hours to days)
- Active: propose blocks and attest to blocks
- Exit: voluntary or forced (slashing)

## Slashing Conditions
1. **Double voting**: Signing two different attestations for the same target epoch
2. **Surround voting**: Signing an attestation that "surrounds" another attestation
3. **Double block proposal**: Proposing two different blocks for the same slot

Slashing penalty: at least 1/32 of staked ETH, plus correlation penalty if many validators are slashed simultaneously.

## Attestation Performance
- Each epoch (~6.4 minutes), every active validator must produce an attestation
- Attestation includes: source, target, and head votes
- Missed attestations result in small penalties (inactivity leak)
- Attestation inclusion delay matters: sooner is better

## Sync Committee
- 512 validators randomly selected every ~27 hours
- Higher rewards but requires being online
- Missing sync committee duties results in penalties

## Rewards
- Base reward depends on total staked ETH
- Proposer rewards: for including attestations and sync committee signatures
- MEV rewards: tips from transaction ordering (via MEV-Boost)

## Key Metrics to Monitor
- Attestation effectiveness (>95% is good)
- Proposal duties (1 every ~2 months per validator)
- Sync committee participation
- Balance trend over time
