"""Health check functions — pure, stateless evaluation.

Takes raw data from StatusMonitor and produces structured HealthCheck results.
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthLevel(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    name: str
    level: HealthLevel
    message: str
    value: Any = None
    details: Optional[Dict[str, Any]] = None
    auto_fixable: bool = False
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level.value,
            "message": self.message,
            "value": self.value,
            "details": self.details,
            "auto_fixable": self.auto_fixable,
            "timestamp": self.timestamp,
        }


@dataclass
class HealthReport:
    overall: HealthLevel
    checks: List[HealthCheck]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": self.overall.value,
            "checks": [c.to_dict() for c in self.checks],
            "timestamp": self.timestamp,
        }


class HealthMonitor:
    """Stateless health check functions. Mirrors core/system/checker.py pattern."""

    @staticmethod
    def check_containers(containers: List[Dict[str, Any]]) -> HealthCheck:
        if not containers:
            return HealthCheck(
                name="container_liveness", level=HealthLevel.CRITICAL,
                message="No containers found",
                auto_fixable=False,
            )

        running = [c for c in containers if c.get("State") == "running"]
        stopped = [c for c in containers if c.get("State") not in ("running", "restarting")]
        restarting = [c for c in containers if c.get("State") == "restarting"]

        if len(running) == len(containers):
            return HealthCheck(
                name="container_liveness", level=HealthLevel.HEALTHY,
                message=f"All {len(running)} containers running",
                value={"running": len(running), "total": len(containers)},
            )

        if stopped:
            stopped_names = [c.get("Service", "?") for c in stopped]
            return HealthCheck(
                name="container_liveness", level=HealthLevel.CRITICAL,
                message=f"Container(s) down: {', '.join(stopped_names)}",
                value={"running": len(running), "total": len(containers)},
                details={"stopped_services": stopped_names},
                auto_fixable=True,
            )

        if restarting:
            names = [c.get("Service", "?") for c in restarting]
            return HealthCheck(
                name="container_liveness", level=HealthLevel.DEGRADED,
                message=f"Container(s) restarting: {', '.join(names)}",
                value={"running": len(running), "total": len(containers)},
                details={"restarting_services": names},
            )

        return HealthCheck(
            name="container_liveness", level=HealthLevel.DEGRADED,
            message=f"{len(running)}/{len(containers)} containers running",
            value={"running": len(running), "total": len(containers)},
        )

    @staticmethod
    def check_el_sync(el_status: Dict[str, Any], max_distance: int) -> HealthCheck:
        if el_status.get("error"):
            return HealthCheck(
                name="el_sync", level=HealthLevel.CRITICAL,
                message=f"Execution layer unreachable: {el_status['error']}",
            )
        if el_status.get("syncing") is False:
            return HealthCheck(
                name="el_sync", level=HealthLevel.HEALTHY,
                message=f"EL synced (block {el_status.get('current_block', '?')})",
                value=el_status,
            )
        if el_status.get("syncing"):
            highest = el_status.get("highest_block", 0)
            current = el_status.get("current_block", 0)
            distance = highest - current if highest > current else 0
            level = HealthLevel.DEGRADED if distance > max_distance else HealthLevel.HEALTHY
            return HealthCheck(
                name="el_sync", level=level,
                message=f"EL syncing: {el_status.get('progress_pct', 0):.1f}% ({distance} blocks behind)",
                value=el_status,
            )
        return HealthCheck(
            name="el_sync", level=HealthLevel.DEGRADED,
            message="EL sync status unknown",
        )

    @staticmethod
    def check_cl_sync(cl_status: Dict[str, Any], max_distance: int) -> HealthCheck:
        if cl_status.get("error"):
            return HealthCheck(
                name="cl_sync", level=HealthLevel.CRITICAL,
                message=f"Consensus layer unreachable: {cl_status['error']}",
            )
        if cl_status.get("syncing") is False:
            return HealthCheck(
                name="cl_sync", level=HealthLevel.HEALTHY,
                message=f"CL synced (slot {cl_status.get('head_slot', '?')})",
                value=cl_status,
            )
        if cl_status.get("syncing"):
            distance = cl_status.get("sync_distance", 0)
            level = HealthLevel.DEGRADED if distance > max_distance else HealthLevel.HEALTHY
            return HealthCheck(
                name="cl_sync", level=level,
                message=f"CL syncing: {cl_status.get('progress_pct', 0):.1f}% ({distance} slots behind)",
                value=cl_status,
            )
        return HealthCheck(
            name="cl_sync", level=HealthLevel.DEGRADED,
            message="CL sync status unknown",
        )

    @staticmethod
    def check_el_peers(eth_docker_path: str, min_peers: int) -> HealthCheck:
        count = _query_el_peer_count(eth_docker_path)
        if count is None:
            return HealthCheck(
                name="el_peers", level=HealthLevel.DEGRADED,
                message="EL peer count unavailable",
            )
        level = HealthLevel.HEALTHY if count >= min_peers else HealthLevel.DEGRADED
        return HealthCheck(
            name="el_peers", level=level,
            message=f"EL peers: {count}",
            value={"count": count, "min": min_peers},
        )

    @staticmethod
    def check_cl_peers(eth_docker_path: str, min_peers: int) -> HealthCheck:
        count = _query_cl_peer_count(eth_docker_path)
        if count is None:
            return HealthCheck(
                name="cl_peers", level=HealthLevel.DEGRADED,
                message="CL peer count unavailable",
            )
        level = HealthLevel.HEALTHY if count >= min_peers else HealthLevel.DEGRADED
        return HealthCheck(
            name="cl_peers", level=level,
            message=f"CL peers: {count}",
            value={"count": count, "min": min_peers},
        )

    @classmethod
    def full_report(
        cls,
        containers: List[Dict[str, Any]],
        el_sync: Dict[str, Any],
        cl_sync: Dict[str, Any],
        eth_docker_path: str,
        thresholds: Dict[str, Any],
    ) -> HealthReport:
        # Run peer checks in parallel (each is a subprocess call)
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_el_peers = pool.submit(cls.check_el_peers, eth_docker_path, thresholds.get("min_el_peers", 3))
            f_cl_peers = pool.submit(cls.check_cl_peers, eth_docker_path, thresholds.get("min_cl_peers", 3))

        checks = [
            cls.check_containers(containers),
            cls.check_el_sync(el_sync, thresholds.get("el_max_sync_distance", 50)),
            cls.check_cl_sync(cl_sync, thresholds.get("cl_max_sync_distance", 10)),
            f_el_peers.result(),
            f_cl_peers.result(),
        ]
        worst = max(
            (c.level for c in checks),
            key=lambda lv: (HealthLevel.HEALTHY, HealthLevel.DEGRADED, HealthLevel.CRITICAL).index(lv),
            default=HealthLevel.HEALTHY,
        )
        return HealthReport(overall=worst, checks=checks)


# ---------------------------------------------------------------------------
# Peer count helpers — reuse _docker_exec_wget from core/node/status.py
# ---------------------------------------------------------------------------

def _docker_exec_wget(eth_docker_path: str, service: str, url: str,
                      post_data: Optional[str] = None) -> Any:
    """Wrapper that delegates to StatusMonitor's pattern."""
    from core.node.status import StatusMonitor
    sm = StatusMonitor(eth_docker_path)
    return sm._docker_exec_wget(service, url, post_data)


def _query_el_peer_count(eth_docker_path: str) -> Optional[int]:
    data = _docker_exec_wget(
        eth_docker_path, "execution", "http://localhost:8545",
        post_data='{"jsonrpc":"2.0","method":"net_peerCount","params":[],"id":1}',
    )
    if data and isinstance(data, dict):
        hex_val = data.get("result")
        if hex_val:
            try:
                return int(hex_val, 16)
            except (ValueError, TypeError):
                pass
    return None


def _query_cl_peer_count(eth_docker_path: str) -> Optional[int]:
    data = _docker_exec_wget(
        eth_docker_path, "consensus", "http://localhost:5052/eth/v1/node/peer_count",
    )
    if data and isinstance(data, dict):
        peer_data = data.get("data", {})
        connected = peer_data.get("connected")
        if connected is not None:
            try:
                return int(connected)
            except (ValueError, TypeError):
                pass
    return None
