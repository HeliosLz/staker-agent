"""TodoWrite — structured task tracking for multi-step operations (s03 pattern).

The LLM creates and updates a task list via the `todo` tool. Only one task
can be in_progress at a time, enforcing sequential focus. A nag reminder
fires if the LLM goes 3+ turns without updating the list.
"""
from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional


class TodoManager:
    """Per-session todo list. Thread-safe."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: List[Dict[str, str]] = []
        self._turns_since_update: int = 0

    def update(self, items: List[Dict[str, str]]) -> str:
        """Replace the entire todo list. Returns rendered view.

        Each item: {"id": str, "text": str, "status": "pending"|"in_progress"|"completed"}
        Constraint: at most one item can be in_progress.
        """
        # Validate
        in_progress_count = sum(1 for i in items if i.get("status") == "in_progress")
        if in_progress_count > 1:
            return "Error: only one task can be in_progress at a time."

        for item in items:
            if item.get("status") not in ("pending", "in_progress", "completed"):
                return f"Error: invalid status '{item.get('status')}' for task '{item.get('id')}'"

        with self._lock:
            self._items = list(items)  # defensive copy
            self._turns_since_update = 0

        return self.render()

    def render(self) -> str:
        """Render the current todo list as text."""
        with self._lock:
            if not self._items:
                return "(no tasks)"
            lines = []
            for item in self._items:
                status = item.get("status", "pending")
                icon = {"completed": "[x]", "in_progress": "[>]", "pending": "[ ]"}.get(status, "[ ]")
                lines.append(f"{icon} {item.get('id', '?')}: {item.get('text', '')}")
            return "\n".join(lines)

    def tick_turn(self) -> None:
        """Increment the turn counter. Called once per LLM turn."""
        with self._lock:
            self._turns_since_update += 1

    def should_nag(self) -> bool:
        """Return True if the LLM should be reminded to update todos."""
        with self._lock:
            return self._turns_since_update >= 3 and self._has_open_tasks()

    def _has_open_tasks(self) -> bool:
        return any(i.get("status") != "completed" for i in self._items)

    def is_empty(self) -> bool:
        with self._lock:
            return len(self._items) == 0

    def get_items(self) -> List[Dict[str, str]]:
        with self._lock:
            return list(self._items)
