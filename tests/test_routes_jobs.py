import sys
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import api.routes as routes
import core.jobs as jobs


class FakeModeManager:
    _mode = "supervised"

    @staticmethod
    def current():
        return FakeModeManager._mode

    @staticmethod
    def set(mode):
        FakeModeManager._mode = mode
        return {"mode": mode}

    @staticmethod
    def requires_approval(step):
        return step in ("ideas", "script", "video", "metadata", "upload")


class FakeTTS:
    async def generate(self, text, filename=None, voice=None):
        return Path("/tmp/fake_audio.mp3")


def _client():
    app = FastAPI()
    app.include_router(routes.router, prefix="/api")
    return TestClient(app)


async def _fake_metadata(script, idea=None, language=None):
    return {"title": "Meta"}


@pytest.fixture(autouse=True)
def _isolate(monkeypatch, tmp_path):
    profile = {"mode": "supervised", "niche": "", "style_preferences": {}, "autonomous_upload_allowed": False}
    monkeypatch.setattr(routes, "load_user_profile", lambda: dict(profile))
    monkeypatch.setattr(routes, "save_user_profile", lambda p: profile.update(p))
    monkeypatch.setattr(routes, "ModeManager", FakeModeManager)
    monkeypatch.setattr(routes, "TTSProvider", FakeTTS)
    monkeypatch.setattr(routes, "add_item", lambda **kwargs: {"id": "lib-1"})
    monkeypatch.setattr(routes, "list_items", lambda item_type=None, limit=50: [])
    monkeypatch.setattr(routes, "is_youtube_configured", lambda: False)
    monkeypatch.setattr(routes, "generate_metadata", _fake_metadata)
    monkeypatch.setattr(routes, "create_thumbnail", lambda *a, **kwargs: Path("/tmp/t.jpg"))
    # Aisla jobs a tmp para no contaminar data/jobs.json real
    monkeypatch.setattr(jobs, "JOBS_FILE", tmp_path / "jobs.json")
    yield
    jobs._jobs.clear()


def _wait_for_job(client, job_id, timeout=5.0):
    deadline = time.time() + timeout
    body = {}
    while time.time() < deadline:
        body = client.get(f"/api/jobs/{job_id}").json()
        if body["status"] in ("succeeded", "failed"):
            return body
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} did not finish; last state: {body}")


def test_super_pipeline_async_returns_a_job(monkeypatch):
    monkeypatch.setattr(routes, "generate_subtitles", lambda script, title="subtitles", audio_path=None: {"srt_path": "s.srt", "vtt_path": "s.vtt"})
    monkeypatch.setattr(routes, "create_video_from_script_and_audio", lambda **kwargs: {"video_path": "v.mp4"})

    client = _client()
    response = client.post("/api/super_pipeline_async", json={"script": "guion", "title": "t"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["job_id"].startswith("job_")
    assert body["poll"] == f"/api/jobs/{body['job_id']}"

    final = _wait_for_job(client, body["job_id"])
    assert final["status"] == "succeeded"
    assert final["result"]["video_path"] == "v.mp4"
    assert final["result"]["audio_path"] == "/tmp/fake_audio.mp3"


def test_super_pipeline_async_captures_pipeline_failures(monkeypatch):
    monkeypatch.setattr(routes, "generate_subtitles", lambda *a, **k: {"srt_path": "s.srt", "vtt_path": "s.vtt"})

    def boom(**kwargs):
        raise RuntimeError("ffmpeg explode")

    monkeypatch.setattr(routes, "create_video_from_script_and_audio", boom)

    client = _client()
    body = client.post("/api/super_pipeline_async", json={"script": "g", "title": "t"}).json()
    final = _wait_for_job(client, body["job_id"])
    assert final["status"] == "failed"
    assert "ffmpeg explode" in final["error"]


def test_jobs_listing_and_unknown_id(monkeypatch):
    monkeypatch.setattr(routes, "generate_subtitles", lambda *a, **k: {"srt_path": "s.srt", "vtt_path": "s.vtt"})
    monkeypatch.setattr(routes, "create_video_from_script_and_audio", lambda **k: {"video_path": "v.mp4"})

    client = _client()
    created = client.post("/api/super_pipeline_async", json={"script": "g", "title": "t"}).json()
    finished = _wait_for_job(client, created["job_id"])

    listing = client.get("/api/jobs").json()["jobs"]
    assert listing and listing[0]["id"] == created["job_id"]
    assert client.get("/api/jobs/nope").status_code == 404


def test_super_pipeline_blocking_endpoint_still_works(monkeypatch):
    monkeypatch.setattr(routes, "generate_subtitles", lambda *a, **k: {"srt_path": "s.srt", "vtt_path": "s.vtt"})
    monkeypatch.setattr(routes, "create_video_from_script_and_audio", lambda **k: {"video_path": "v.mp4"})

    body = _client().post("/api/super_pipeline", json={"script": "guion", "title": "t"}).json()
    assert body["success"] is True
    assert body["video_path"] == "v.mp4"
