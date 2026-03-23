---
name: troubleshooting
description: Common node issues, diagnostics, and fixes
---

# Node Troubleshooting Guide

## Container Not Starting
- Check docker logs: `docker compose logs <service>`
- Common cause: port conflict (8545, 5052, 30303)
- Fix: stop conflicting service or change ports in .env

## EL/CL Not Syncing
- Initial sync can take hours to days depending on network
- Check peer count: need at least 3-5 peers
- If stuck at 0 peers: firewall blocking P2P ports (30303 TCP/UDP for EL, 9000 TCP/UDP for CL)
- China-specific: ISP may throttle/block P2P traffic, consider VPN/tunnel

## Low Peer Count
- Open P2P ports: 30303 (EL), 9000 (CL)
- Check router UPnP or manual port forwarding
- Verify with: `docker compose exec execution wget -qO- http://localhost:8545` (net_peerCount)
- Behind NAT: consider `--nat extip:<your-public-ip>` flag

## High Disk Usage
- Mainnet Geth: ~1.5TB and growing
- Prune Geth: `docker compose run --rm execution geth snapshot prune-state`
- Monitor disk: df -h ~/eth-docker

## Memory Issues
- Geth recommended: 16GB+ RAM for mainnet
- Teku is more memory-hungry than Lighthouse
- Check OOM kills: `dmesg | grep -i oom`
- Reduce cache: set `--cache` flag lower in docker-compose override

## Missed Attestations
- Ensure both EL and CL are synced
- Check time sync: `timedatectl` — NTP must be enabled
- Network latency: high ping to peers causes late attestations
- Validator client must be running and connected to beacon node

## Database Corruption
- Symptoms: container crash loops, error logs mentioning "corruption"
- Fix: resync from scratch (`docker compose down -v` then `docker compose up -d`)
- Prevention: use UPS to prevent unclean shutdown

## eth-docker Specific
- Config regeneration: `cd ~/eth-docker && ./ethd config`
- Update clients: `cd ~/eth-docker && ./ethd update`
- View all services: `docker compose ps`
- Restart single service: `docker compose restart <service>`
