"""Autonomous Monitor Loop (s11 pattern).

Rules-driven background loop. No LLM — decisions are deterministic.
Shares tools and state with the Chat Loop via ToolContext and notification queue.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from queue import Queue
from typing import Any, Callable, Dict, List, Optional

from core.agent.notifier import format_event
from core.agent.state import ActionRecord, AgentState
from core.agent.tools import ToolContext, execute
from core.monitor.health import HealthLevel, HealthMonitor, HealthReport

logger = logging.getLogger(__name__)


@dataclass
class MonitorConfig:
    check_interval: int = 60
    alert_cooldown: int = 300
    max_auto_actions: int = 3
    thresholds: Dict[str, Any] = field(default_factory=lambda: {
        "el_max_sync_distance": 50,
        "cl_max_sync_distance": 10,
        "min_el_peers": 3,
        "min_cl_peers": 3,
    })


class MonitorLoop:
    """Background daemon that watches node health and auto-remediates."""

    def __init__(
        self,
        ctx: ToolContext,
        notif_queue: Queue,
        config: MonitorConfig,
    ) -> None:
        self.ctx = ctx
        self.notif_queue = notif_queue  # s08: Chat Loop drains this
        self.config = config
        self._sinks: List[Callable[[str], None]] = []
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._memory_store: Any = None  # MemoryStore — set via DI
        # WebSocket push (set after Flask init)
        self._socketio: Any = None
        self._flask_app: Any = None

    def add_sink(self, sink: Callable[[str], None]) -> None:
        self._sinks.append(sink)

    def set_memory_store(self, memory_store: Any) -> None:
        self._memory_store = memory_store

    def set_socketio(self, socketio: Any, app: Any) -> None:
        self._socketio = socketio
        self._flask_app = app

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Monitor loop started (interval=%ds)", self.config.check_interval)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("Monitor loop stopped")

    def _run(self) -> None:
        # Run first check immediately
        self._safe_tick()
        while not self._stop.wait(self.config.check_interval):
            self._safe_tick()

    def _safe_tick(self) -> None:
        try:
            self.tick()
        except Exception:
            logger.error("Monitor tick failed", exc_info=True)

    def tick(self) -> None:
        """One complete cycle: sense -> decide -> act."""
        state = self.ctx.state
        sm = self.ctx.status_monitor
        if not sm or not state:
            return

        # 1. Sense
        containers = sm.get_container_status()
        sync = sm.get_sync_status()

        report = HealthMonitor.full_report(
            containers,
            sync.get("execution", {}),
            sync.get("consensus", {}),
            self.ctx.eth_docker_path,
            self.config.thresholds,
        )
        state.last_report = report.to_dict()

        # 2. Decide + Act
        for check in report.checks:
            self._process_check(check, state)

        # 3. Push to WebSocket
        self._push_ws(report)

    def _process_check(self, check: Any, state: AgentState) -> None:
        alert = state.get_alert(check.name)

        if check.level == HealthLevel.HEALTHY:
            if alert and not alert.recovered:
                downtime = time.time() - alert.fired_at
                state.record_recovery(check.name)
                self._emit("recovery", check, downtime=downtime)
            return

        # DEGRADED or CRITICAL
        if alert is None:
            # New issue
            if check.auto_fixable and check.level == HealthLevel.CRITICAL:
                service = self._fixable_service(check)
                if service:
                    execute("restart_service", {"service": service}, self.ctx)
                    state.fire_alert(check.name, check.level.value, check.message)
                    state.record_action(ActionRecord(
                        timestamp=time.time(), action_type="auto_restart",
                        target=check.name, detail=f"Auto-restarted {service}",
                    ))
                    self._emit("auto_fix", check)
                    return
            state.fire_alert(check.name, check.level.value, check.message)
            self._emit("alert", check)

        elif check.auto_fixable and alert.action_count >= self.config.max_auto_actions:
            if not alert.escalated:
                alert.escalated = True
                self._emit("escalation", check, action_count=alert.action_count)

        elif self._cooldown_expired(alert):
            if check.auto_fixable:
                service = self._fixable_service(check)
                if service:
                    execute("restart_service", {"service": service}, self.ctx)
                    state.record_action(ActionRecord(
                        timestamp=time.time(), action_type="auto_restart",
                        target=check.name, detail=f"Auto-restarted {service}",
                    ))
            state.update_alert(check.name, check.level.value, check.message)
            self._emit("alert", check)

    def _cooldown_expired(self, alert: Any) -> bool:
        return (time.time() - alert.last_notified) > self.config.alert_cooldown

    @staticmethod
    def _fixable_service(check: Any) -> Optional[str]:
        if not check.details:
            return None
        services = check.details.get("stopped_services", [])
        return services[0] if services else None

    def _emit(self, event_type: str, check: Any, **extra: Any) -> None:
        event: Dict[str, Any] = {
            "type": event_type,
            "check": check.name,
            "level": check.level.value,
            "message": check.message,
            "timestamp": time.time(),
            **extra,
        }
        # s08: push to notification queue for Chat Loop to drain
        self.notif_queue.put(event)
        # Persist incident to memory store
        if self._memory_store:
            try:
                key = f"{event_type}_{check.name}"
                content = check.message
                if check.level.value:
                    content = f"[{check.level.value}] {content}"
                self._memory_store.save("incidents", key, content)
            except Exception:
                logger.debug("Memory incident recording failed", exc_info=True)
        # Push to registered sinks (Telegram, etc.)
        formatted = format_event(event)
        for sink in self._sinks:
            try:
                sink(formatted)
            except Exception:
                logger.warning("Notification sink failed", exc_info=True)

    def _push_ws(self, report: HealthReport) -> None:
        if self._socketio and self._flask_app:
            try:
                with self._flask_app.app_context():
                    self._socketio.emit(
                        "health_update", report.to_dict(),
                        room="health_updates",
                    )
            except Exception:
                logger.debug("WebSocket health push failed", exc_info=True)
