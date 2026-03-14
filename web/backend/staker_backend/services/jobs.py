"""Job management service."""
from __future__ import annotations

from typing import Dict, List

from ..jobs import Job, JobManager


class JobService:
    """Expose job metadata to API layer."""

    def __init__(self, manager: JobManager) -> None:
        self._manager = manager

    def submit(self, name: str, func, *, args=None, kwargs=None, on_success=None, on_failure=None) -> Job:
        return self._manager.submit(
            name,
            func,
            args=args,
            kwargs=kwargs,
            on_success=on_success,
            on_failure=on_failure,
        )

    def get(self, job_id: str) -> Dict[str, object] | None:
        job = self._manager.get(job_id)
        return job.to_dict() if job else None

    def list(self) -> List[Dict[str, object]]:
        jobs = self._manager.list()
        return [job.to_dict() for job in jobs.values()]
