"""Shared Agent State — read/written by both Monitor Loop and Chat Loop."""
from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AlertRecord:
    """Tracks the lifecycle of a single alert."""
    name: str
    level: str               # "degraded" | "critical"
    message: str
    fired_at: float = field(default_factory=time.time)
    last_notified: float = 0.0
    action_count: int = 0
    escalated: bool = False
    recovered: bool = False


@dataclass
class ActionRecord:
    """Log entry for an action taken by the agent."""
    timestamp: float
    action_type: str          # "auto_restart" | "alert" | "recovery" | "escalation"
    target: str               # check name or service name
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "action_type": self.action_type,
            "target": self.target,
            "detail": self.detail,
        }


class AgentState:
    """Runtime state shared between Monitor Loop and Chat Loop. Thread-safe."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.last_report: Optional[Dict[str, Any]] = None
        self.alerts: Dict[str, AlertRecord] = {}
        self.action_log: deque[ActionRecord] = deque(maxlen=200)
        self.started_at: float = time.time()

    def get_alert(self, name: str) -> Optional[AlertRecord]:
        with self._lock:
            return self.alerts.get(name)

    def fire_alert(self, name: str, level: str, message: str) -> AlertRecord:
        now = time.time()
        with self._lock:
            record = AlertRecord(
                name=name, level=level, message=message,
                fired_at=now, last_notified=now,
            )
            self.alerts[name] = record
            return record

    def update_alert(self, name: str, level: str, message: str) -> Optional[AlertRecord]:
        now = time.time()
        with self._lock:
            record = self.alerts.get(name)
            if record:
                record.level = level
                record.message = message
                record.last_notified = now
                record.recovered = False
            return record

    def record_recovery(self, name: str) -> Optional[AlertRecord]:
        with self._lock:
            record = self.alerts.get(name)
            if record:
                record.recovered = True
            # Prune old recovered alerts to prevent unbounded growth
            self._prune_recovered()
            return record

    def _prune_recovered(self) -> None:
        """Remove recovered alerts older than 1 hour. Must be called with lock held."""
        cutoff = time.time() - 3600
        stale = [k for k, v in self.alerts.items()
                 if v.recovered and v.fired_at < cutoff]
        for k in stale:
            del self.alerts[k]

    def record_action(self, action: ActionRecord) -> None:
        with self._lock:
            self.action_log.append(action)
            # Also bump action_count on the related alert
            alert = self.alerts.get(action.target)
            if alert and action.action_type == "auto_restart":
                alert.action_count += 1

    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self.action_log)[-limit:]
        return [a.to_dict() for a in items]

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                {
                    "name": r.name, "level": r.level, "message": r.message,
                    "fired_at": r.fired_at, "action_count": r.action_count,
                    "escalated": r.escalated, "recovered": r.recovered,
                }
                for r in self.alerts.values()
            ]
