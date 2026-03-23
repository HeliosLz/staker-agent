"""Persistent memory store for the Staker Agent.

Disk-backed memory that survives restarts. Stores user preferences,
incident history, and operator notes. No Flask dependency.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

VALID_CATEGORIES = ("preferences", "incidents", "notes")
MAX_INCIDENTS = 50  # ring-buffer cap


class MemoryStore:
    """Thread-safe, disk-persisted memory for the agent."""

    def __init__(self, storage_dir: str) -> None:
        self._dir = Path(storage_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        # Warm cache from disk
        self._cache: Dict[str, Any] = {}
        for cat in VALID_CATEGORIES:
            self._cache[cat] = self._load(cat)
        # Dirty-flag cache for get_context()
        self._context_cache: str = ""
        self._context_dirty: bool = True

    # ------------------------------------------------------------------
    # LLM tool interface
    # ------------------------------------------------------------------

    def save(self, category: str, key: str, content: str) -> None:
        """Save a memory entry. category: preferences|incidents|notes."""
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}. Must be one of {VALID_CATEGORIES}")
        with self._lock:
            data = self._cache[category]
            if category == "preferences":
                data[key] = content
            else:
                entry = {"ts": time.time(), "key": key, "content": content}
                data.append(entry)
                if category == "incidents" and len(data) > MAX_INCIDENTS:
                    self._cache[category] = data[-MAX_INCIDENTS:]
            self._context_dirty = True
            snapshot = self._cache[category]
        self._flush(category, snapshot)

    def recall(self, query: str = "", category: str = "") -> List[Dict[str, Any]]:
        """Retrieve memories. Filter by category and/or keyword search."""
        results: List[Dict[str, Any]] = []
        cats = [category] if category and category in VALID_CATEGORIES else list(VALID_CATEGORIES)
        query_lower = query.lower()
        with self._lock:
            for cat in cats:
                data = self._cache[cat]
                if cat == "preferences":
                    for k, v in data.items():
                        if not query_lower or query_lower in k.lower() or query_lower in str(v).lower():
                            results.append({"category": cat, "key": k, "content": v})
                else:
                    for entry in data:
                        if not query_lower or query_lower in entry.get("key", "").lower() or query_lower in str(entry.get("content", "")).lower():
                            results.append({"category": cat, **entry})
        return results

    def forget(self, category: str, key: str) -> bool:
        """Delete a memory entry by category and key."""
        if category not in VALID_CATEGORIES:
            return False
        with self._lock:
            data = self._cache[category]
            if category == "preferences":
                if key not in data:
                    return False
                del data[key]
            else:
                before = len(data)
                self._cache[category] = [e for e in data if e.get("key") != key]
                if len(self._cache[category]) == before:
                    return False
            self._context_dirty = True
            snapshot = self._cache[category]
        self._flush(category, snapshot)
        return True

    # ------------------------------------------------------------------
    # System interface
    # ------------------------------------------------------------------

    def get_context(self, max_tokens: int = 500) -> str:
        """Return a compressed summary for system prompt injection.

        Priority: preferences > recent incidents > notes.
        Uses a dirty flag to avoid rebuilding when nothing changed.
        """
        with self._lock:
            if not self._context_dirty:
                return self._context_cache

            parts: List[str] = []
            char_budget = max_tokens * 3

            prefs = self._cache["preferences"]
            if prefs:
                pref_lines = [f"- {k}: {v}" for k, v in prefs.items()]
                parts.append("用户偏好:\n" + "\n".join(pref_lines))

            incidents = self._cache["incidents"]
            if incidents:
                recent = incidents[-5:]
                inc_lines = []
                for inc in recent:
                    ts = time.strftime("%m-%d %H:%M", time.localtime(inc.get("ts", 0)))
                    inc_lines.append(f"- [{ts}] {inc.get('key', '')}: {inc.get('content', '')}")
                parts.append("近期事件:\n" + "\n".join(inc_lines))

            notes = self._cache["notes"]
            if notes:
                recent_notes = notes[-5:]
                note_lines = [f"- {n.get('key', '')}: {n.get('content', '')}" for n in recent_notes]
                parts.append("运维笔记:\n" + "\n".join(note_lines))

            if not parts:
                self._context_cache = ""
            else:
                result = "\n\n".join(parts)
                if len(result) > char_budget:
                    result = result[:char_budget] + "\n..."
                self._context_cache = result

            self._context_dirty = False
            return self._context_cache

    # ------------------------------------------------------------------
    # Internal I/O
    # ------------------------------------------------------------------

    def _path(self, category: str) -> Path:
        return self._dir / f"{category}.json"

    def _load(self, category: str) -> Any:
        try:
            return json.loads(self._path(category).read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {} if category == "preferences" else []
        except (json.JSONDecodeError, OSError):
            logger.warning("Failed to load memory file %s, starting fresh", self._path(category))
            return {} if category == "preferences" else []

    def _flush(self, category: str, data: Any) -> None:
        """Write data snapshot to disk. Called outside the lock."""
        path = self._path(category)
        try:
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            logger.error("Failed to write memory file %s", path, exc_info=True)
