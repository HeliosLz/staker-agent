"""Background job manager for long-running tasks."""
from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, Optional

from flask import Flask, current_app

from ..extensions import socketio


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    name: str
    status: JobStatus
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    result: Any = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result": self.result,
            "error": self.error,
        }


class JobManager:
    """Minimal in-memory job queue for background tasks."""

    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
        self._subscribers: list[Callable[[Job], None]] = []
        self._logger = logging.getLogger(__name__)

    def submit(
        self,
        name: str,
        target: Callable[..., Any],
        *,
        args: Iterable[Any] | None = None,
        kwargs: Dict[str, Any] | None = None,
        on_success: Callable[[Job, Any], None] | None = None,
        on_failure: Callable[[Job, BaseException], None] | None = None,
    ) -> Job:
        job_id = str(uuid.uuid4())
        job = Job(id=job_id, name=name, status=JobStatus.PENDING)
        with self._lock:
            self._jobs[job_id] = job
        self._notify(job)

        args = tuple(args or ())
        kwargs = dict(kwargs or {})

        thread = threading.Thread(
            target=self._run_job,
            args=(job, target, args, kwargs, on_success, on_failure),
            daemon=True,
        )
        thread.start()
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> Dict[str, Job]:
        with self._lock:
            return dict(self._jobs)

    def subscribe(self, callback: Callable[[Job], None]) -> None:
        with self._lock:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Job], None]) -> None:
        with self._lock:
            self._subscribers = [cb for cb in self._subscribers if cb is not callback]

    def _run_job(
        self,
        job: Job,
        target: Callable[..., Any],
        args: Iterable[Any],
        kwargs: Dict[str, Any],
        on_success: Callable[[Job, Any], None] | None,
        on_failure: Callable[[Job, BaseException], None] | None,
    ) -> None:
        self._update_job(job, status=JobStatus.RUNNING)
        try:
            result = target(*args, **kwargs)
            self._update_job(job, status=JobStatus.SUCCEEDED, result=result)
            if on_success:
                on_success(job, result)
        except BaseException as exc:  # pragma: no cover - defensive
            self._update_job(job, status=JobStatus.FAILED, error=str(exc))
            if on_failure:
                on_failure(job, exc)

    def _update_job(self, job: Job, *, status: JobStatus, result: Any = None, error: Optional[str] = None) -> None:
        with self._lock:
            job.status = status
            job.result = result
            job.error = error
            job.updated_at = time.time()
        self._notify(job)

    def _notify(self, job: Job) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for callback in subscribers:
            try:
                callback(job)
            except Exception as exc:  # pragma: no cover - defensive
                self._logger.exception("Job subscriber error", exc_info=exc)


def init_jobs(app: Flask) -> JobManager:
    manager = JobManager()
    def emit_update(job: Job) -> None:
        with app.app_context():
            socketio.emit(
                "job_updated",
                job.to_dict(),
            )

    manager.subscribe(emit_update)
    app.extensions["jobs"] = manager
    return manager


def get_job_manager() -> JobManager:
    manager = current_app.extensions.get("jobs")
    if not isinstance(manager, JobManager):
        raise RuntimeError("Job manager not initialised")
    return manager
