"""Persistent memory store for the Staker Agent.

Disk-backed memory that survives restarts. Stores user preferences,
incident history, and operator notes. No Flask dependency.

Recall uses hybrid search: keyword token overlap + semantic embedding similarity.
Embedding function is injected via set_embed_fn() (DI). Falls back to keyword-only
when no embed_fn is available.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

VALID_CATEGORIES = ("preferences", "incidents", "notes")
MAX_INCIDENTS = 50  # ring-buffer cap

# Tokenizer: English words / numbers + individual CJK characters
_TOKEN_RE = re.compile(r'[a-zA-Z0-9]+|[\u4e00-\u9fff\u3400-\u4dbf]', re.UNICODE)

# Hybrid search weights
_KEYWORD_WEIGHT = 0.4
_SEMANTIC_WEIGHT = 0.6
_MIN_SCORE = 0.01

_EMBED_FLUSH_DELAY = 5.0  # seconds — debounce window for embedding persistence


class MemoryStore:
    """Thread-safe, disk-persisted memory with hybrid search."""

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
        # Embedding support (DI)
        self._embed_fn: Optional[Callable[[str], List[float]]] = None
        self._embed_model: str = ""
        self._embeddings: Dict[str, List[float]] = {}
        self._load_embeddings()
        # Background embedding: single worker to avoid blocking callers
        self._embed_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="embed")
        # Debounced flush for embeddings
        self._embed_flush_pending: bool = False
        self._embed_flush_timer: Optional[threading.Timer] = None

    def set_embed_fn(self, fn: Callable[[str], List[float]], model: str = "") -> None:
        """Inject embedding function. Called from init_services (DI)."""
        self._embed_fn = fn
        if model != self._embed_model:
            with self._lock:
                self._embed_model = model
                self._embeddings.clear()
            self._do_flush_embeddings()

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
        # Compute embedding in background (non-blocking, graceful on failure)
        if self._embed_fn:
            self._embed_executor.submit(self._embed_and_cache, f"{key} {content}")

    def recall(self, query: str = "", category: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Hybrid search: keyword token overlap + semantic similarity.

        Falls back to keyword-only when embed_fn is not available.
        Returns entries sorted by relevance score (highest first).
        """
        candidates = self._collect_candidates(category)
        if not query:
            return candidates[-limit:]

        query_tokens = self._tokenize(query)
        query_emb = self._compute_embedding(query)

        # Snapshot embeddings once to avoid per-entry lock acquisition
        with self._lock:
            emb_snapshot = dict(self._embeddings)

        scored: List[tuple[float, Dict[str, Any]]] = []
        for entry in candidates:
            text = f"{entry.get('key', '')} {entry.get('content', '')}"

            kw = self._keyword_score(query_tokens, self._tokenize(text))

            sem = 0.0
            entry_emb = None
            if query_emb is not None:
                entry_emb = emb_snapshot.get(self._embed_key(text))
                if entry_emb:
                    sem = self._cosine_sim(query_emb, entry_emb)

            # Hybrid only when both sides have embeddings; keyword-only otherwise
            if query_emb is not None and entry_emb is not None:
                score = _KEYWORD_WEIGHT * kw + _SEMANTIC_WEIGHT * sem
            else:
                score = kw

            if score > _MIN_SCORE:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:limit]]

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
    # Search helpers
    # ------------------------------------------------------------------

    def _collect_candidates(self, category: str) -> List[Dict[str, Any]]:
        """Collect all entries from matching categories into a flat list."""
        cats = [category] if category and category in VALID_CATEGORIES else list(VALID_CATEGORIES)
        results: List[Dict[str, Any]] = []
        with self._lock:
            for cat in cats:
                data = self._cache[cat]
                if cat == "preferences":
                    for k, v in data.items():
                        results.append({"category": cat, "key": k, "content": v})
                else:
                    for entry in data:
                        results.append({"category": cat, **entry})
        return results

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Split into tokens. CJK chars become individual tokens."""
        return {t.lower() for t in _TOKEN_RE.findall(text)}

    @staticmethod
    def _keyword_score(query_tokens: set[str], doc_tokens: set[str]) -> float:
        """Token overlap ratio."""
        if not query_tokens:
            return 0.0
        return len(query_tokens & doc_tokens) / len(query_tokens)

    @staticmethod
    def _cosine_sim(a: List[float], b: List[float]) -> float:
        """Cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    @staticmethod
    def _embed_key(text: str) -> str:
        """Stable hash key for embedding cache."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _compute_embedding(self, text: str) -> Optional[List[float]]:
        """Compute embedding via injected function. Returns None on failure."""
        if not self._embed_fn:
            return None
        try:
            return self._embed_fn(text)
        except Exception:
            logger.debug("Embedding computation failed", exc_info=True)
            return None

    def _embed_and_cache(self, text: str) -> None:
        """Compute embedding and persist to cache. Runs on background executor."""
        emb = self._compute_embedding(text)
        if emb is None:
            return
        ek = self._embed_key(text)
        with self._lock:
            self._embeddings[ek] = emb
        self._schedule_flush_embeddings()

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

    def _load_embeddings(self) -> None:
        """Load embedding cache from disk."""
        path = self._dir / "embeddings.json"
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            self._embed_model = raw.get("model", "")
            self._embeddings = raw.get("entries", {})
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self._embeddings = {}
            self._embed_model = ""

    def _schedule_flush_embeddings(self) -> None:
        """Debounced embedding flush — coalesces rapid writes into one disk write."""
        with self._lock:
            if self._embed_flush_pending:
                return
            self._embed_flush_pending = True
        self._embed_flush_timer = threading.Timer(_EMBED_FLUSH_DELAY, self._do_flush_embeddings)
        self._embed_flush_timer.daemon = True
        self._embed_flush_timer.start()

    def _do_flush_embeddings(self) -> None:
        """Actually write embeddings to disk. Called by debounce timer."""
        path = self._dir / "embeddings.json"
        with self._lock:
            self._embed_flush_pending = False
            data = {"model": self._embed_model, "entries": dict(self._embeddings)}
        try:
            path.write_text(json.dumps(data), encoding="utf-8")
        except OSError:
            logger.error("Failed to write embeddings file", exc_info=True)
