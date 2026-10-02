"""
ContentGremlin - Background job registry
Long-running pipeline steps (TTS + video + metadata) run as background jobs in
daemon threads so the API stays responsive. In-memory registry persisted to
data/jobs.json for restoration across restarts (interrupted jobs are marked
as failed on load).
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from core.config import DATA_DIR

JOBS_FILE = DATA_DIR / "jobs.json"
JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)

_MAX_JOBS = 200
_FINISHED = ("succeeded", "failed")
_jobs: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> None:
    """Hydrate persisted jobs; mark interrupted ones as failed."""
    if not JOBS_FILE.exists():
        return
    try:
        data = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return
    if not isinstance(data, list):
        return
    for job in data:
        if not isinstance(job, dict) or "id" not in job:
            continue
        if job.get("status") in ("pending", "running"):
            job["status"] = "failed"
            job["error"] = "interrupted by restart"
            job["updated_at"] = _now()
        _jobs[job["id"]] = job
    _persist()


def _persist() -> None:
    with _lock:
        try:
            ordered = sorted(_jobs.values(), key=lambda j: j.get("created_at", ""), reverse=True)[:_MAX_JOBS]
            JOBS_FILE.write_text(json.dumps(ordered, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        except Exception:
            pass


def _prune() -> None:
    finished = sorted(
        (j for j in _jobs.values() if j.get("status") in _FINISHED),
        key=lambda j: j.get("created_at", ""),
    )
    while len(_jobs) >= _MAX_JOBS and finished:
        del _jobs[finished.pop(0)["id"]]


def create_job(kind: str) -> dict[str, Any]:
    with _lock:
        _prune()
        job = {
            "id": f"job_{uuid.uuid4().hex[:12]}",
            "kind": kind,
            "status": "pending",
            "result": None,
            "error": None,
            "created_at": _now(),
            "updated_at": _now(),
        }
        _jobs[job["id"]] = job
    _persist()
    return job


def _execute_job(job_id: str, fn: Callable[[], Any]) -> dict[str, Any]:
    """Run fn synchronously, recording the outcome on the job. Never raises."""
    job = _jobs[job_id]
    job["status"] = "running"
    job["updated_at"] = _now()
    _persist()
    try:
        result = fn()
    except Exception as error:
        job["status"] = "failed"
        job["error"] = str(error)
    else:
        job["status"] = "succeeded"
        job["result"] = result
    job["updated_at"] = _now()
    _persist()
    return job


def submit_job(kind: str, fn: Callable[[], Any]) -> dict[str, Any]:
    """Create a job and run fn in a background daemon thread. Returns the job snapshot."""
    job = create_job(kind)
    thread = threading.Thread(target=_execute_job, args=(job["id"], fn), daemon=True)
    thread.start()
    return job


def get_job(job_id: str) -> Optional[dict[str, Any]]:
    return _jobs.get(job_id)


def list_jobs(limit: int = 50) -> list[dict[str, Any]]:
    ordered = sorted(_jobs.values(), key=lambda j: j.get("created_at", ""), reverse=True)
    return ordered[:limit]


_load()
