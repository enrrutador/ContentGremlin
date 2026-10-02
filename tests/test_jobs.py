import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.jobs as jobs


@pytest.fixture(autouse=True)
def _isolate(monkeypatch, tmp_path):
    jobs._jobs.clear()
    monkeypatch.setattr(jobs, "JOBS_FILE", tmp_path / "jobs.json")
    yield
    jobs._jobs.clear()


def test_create_job_shape():
    job = jobs.create_job("super_pipeline")
    assert job["id"].startswith("job_")
    assert job["status"] == "pending"
    assert job["result"] is None
    assert job["error"] is None
    assert jobs.get_job(job["id"])["kind"] == "super_pipeline"


def test_execute_job_success_records_result():
    job = jobs.create_job("t")
    done = jobs._execute_job(job["id"], lambda: {"ok": 1})
    assert done["status"] == "succeeded"
    assert done["result"] == {"ok": 1}


def test_execute_job_captures_failures_without_propagating():
    def boom():
        raise RuntimeError("explotó")

    job = jobs.create_job("t")
    done = jobs._execute_job(job["id"], boom)
    assert done["status"] == "failed"
    assert "explotó" in done["error"]


def test_submit_job_runs_in_background_thread_and_completes():
    job = jobs.submit_job("async", lambda: 42)
    assert job["status"] in ("pending", "running")
    deadline = time.time() + 3
    while time.time() < deadline:
        current = jobs.get_job(job["id"])
        if current["status"] in ("succeeded", "failed"):
            assert current["result"] == 42
            return
        time.sleep(0.02)
    pytest.fail("background job stalled")


def test_persistence_roundtrip(tmp_path):
    job = jobs.create_job("t")
    jobs._jobs.clear()
    jobs._load()
    restored = jobs.get_job(job["id"])
    assert restored is not None
    assert restored["kind"] == "t"


def test_stale_running_jobs_are_marked_interrupted():
    job = jobs.create_job("t")
    job["status"] = "running"
    jobs._persist()
    jobs._jobs.clear()
    jobs._load()
    restored = jobs.get_job(job["id"])
    assert restored["status"] == "failed"
    assert restored["error"] == "interrupted by restart"


def test_pruning_drops_oldest_finished_jobs(monkeypatch):
    monkeypatch.setattr(jobs, "_MAX_JOBS", 5)
    old_ids = [jobs.create_job("t")["id"] for _ in range(4)]
    for job in jobs._jobs.values():
        job["status"] = "succeeded"
    jobs.create_job("new")
    newest = jobs.create_job("newer")
    assert len(jobs._jobs) <= 5
    assert jobs.get_job(newest["id"]) is not None
    assert jobs.get_job(old_ids[0]) is None


def test_list_jobs_returns_newest_first_and_respects_limit():
    first = jobs.create_job("a")
    second = jobs.create_job("b")
    rows = jobs.list_jobs()
    assert rows[0]["id"] == second["id"]
    assert {row["id"] for row in jobs.list_jobs(limit=1)} == {second["id"]}
