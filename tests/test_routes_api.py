import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import api.routes as routes


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
    yield
    FakeModeManager._mode = "supervised"


def test_status_endpoint():
    response = _client().get("/api/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "online"
    assert body["mode"] == "supervised"
    assert "safety" in body
    assert "version" in body


def test_mode_endpoints():
    client = _client()
    assert client.get("/api/mode").json()["mode"] == "supervised"

    response = client.post("/api/set_mode", json={"mode": "autonomous"})
    assert response.json()["mode"] == "autonomous"
    assert client.get("/api/mode").json()["mode"] == "autonomous"

    assert client.post("/api/set_mode", json={"mode": "nope"}).status_code == 422


def test_profile_endpoints():
    client = _client()
    base = client.get("/api/profile").json()
    assert base["niche"] == ""

    updated = client.post("/api/profile", json={"niche": "finanzas", "tone": "sobrio"}).json()
    assert updated["profile"]["niche"] == "finanzas"
    assert updated["profile"]["style_preferences"]["tone"] == "sobrio"


def test_public_config_endpoint():
    body = _client().get("/api/config/public").json()
    for key in ("host", "port", "openai_configured", "elevenlabs_configured"):
        assert key in body


def test_safety_endpoint():
    body = _client().get("/api/safety").json()
    assert body["rules_active"] is True
    assert body["can_be_disabled"] is False


def test_analyze_channel_success(monkeypatch):
    monkeypatch.setattr(routes, "analyze_channel", lambda url: {"patterns": {"ok": True}})
    response = _client().post("/api/analyze_channel", json={"channel_url": "@canal"})
    assert response.status_code == 200
    assert response.json()["report"]["patterns"]["ok"] is True


def test_analyze_channel_failure_returns_400(monkeypatch):
    def boom(url):
        raise RuntimeError("yt-dlp failed")

    monkeypatch.setattr(routes, "analyze_channel", boom)
    response = _client().post("/api/analyze_channel", json={"channel_url": "@canal"})
    assert response.status_code == 400
    assert "yt-dlp failed" in response.json()["detail"]


def test_generate_ideas_stores_items(monkeypatch):
    async def fake_ideas(analysis_report, count=8, niche=None):
        return [{"title": "Idea 1"}, {"title": "Idea 2"}]

    monkeypatch.setattr(routes, "generate_ideas", fake_ideas)
    response = _client().post("/api/generate_ideas", json={"analysis_report": {}, "count": 2})
    body = response.json()
    assert body["count"] == 2
    assert len(body["ideas"]) == 2


def test_write_script_returns_script(monkeypatch):
    async def fake_script(idea, language=None):
        return "guion original"

    monkeypatch.setattr(routes, "write_script", fake_script)
    response = _client().post("/api/write_script", json={"idea": {"title": "x"}})
    body = response.json()
    assert body["script"] == "guion original"
    assert body["library_id"] == "lib-1"


def test_generate_voice_endpoint():
    response = _client().post("/api/generate_voice", json={"text": "Texto de prueba", "title": "audio demo"})
    body = response.json()
    assert body["audio_path"] == "/tmp/fake_audio.mp3"


def test_create_video_endpoint(monkeypatch):
    monkeypatch.setattr(
        routes, "create_video_from_script_and_audio",
        lambda **kwargs: {"video_path": "video.mp4", "audio_path": kwargs.get("audio_path")},
    )
    response = _client().post("/api/create_video", json={"audio_path": "a.mp3", "title": "t"})
    assert response.json()["video_path"] == "video.mp4"


def test_full_pipeline_endpoint(monkeypatch):
    monkeypatch.setattr(routes, "create_video_from_script_and_audio", lambda **kwargs: {"video_path": "v.mp4"})
    response = _client().post("/api/full_pipeline", json={"script": "guion", "title": "t"})
    body = response.json()
    assert body["success"] is True
    assert body["video_path"] == "v.mp4"


def test_library_endpoints(monkeypatch):
    monkeypatch.setattr(routes, "get_item", lambda item_id: {"id": item_id} if item_id == "ok" else None)
    monkeypatch.setattr(routes, "delete_item", lambda item_id: item_id == "ok")

    client = _client()
    assert client.get("/api/library").json() == {"items": []}
    assert client.get("/api/library/ok").json()["id"] == "ok"
    assert client.get("/api/library/nope").status_code == 404
    assert client.delete("/api/library/ok").json()["success"] is True
    assert client.delete("/api/library/nope").status_code == 404


def test_generate_subtitles_endpoint(monkeypatch):
    monkeypatch.setattr(
        routes, "generate_subtitles",
        lambda script, title="subtitles", audio_path=None: {"srt_path": "a.srt", "vtt_path": "a.vtt"},
    )
    response = _client().post("/api/generate_subtitles", json={"script": "hola", "title": "demo"})
    assert response.json()["srt_path"] == "a.srt"


def test_generate_metadata_endpoint(monkeypatch):
    async def fake_metadata(script, idea=None, language=None):
        return {"title": "Meta"}

    monkeypatch.setattr(routes, "generate_metadata", fake_metadata)
    response = _client().post("/api/generate_metadata", json={"script": "guion"})
    assert response.json()["metadata"]["title"] == "Meta"


def test_generate_thumbnail_endpoint(monkeypatch, tmp_path):
    monkeypatch.setattr(routes, "create_thumbnail", lambda title, output_name=None: tmp_path / "t.jpg")
    response = _client().post("/api/generate_thumbnail", json={"title": "t"})
    assert "thumbnail_path" in response.json()


def test_upload_permission_error_maps_to_403(monkeypatch):
    def denied(**kwargs):
        raise PermissionError("no allowed")

    monkeypatch.setattr(routes, "upload_video", denied)
    response = _client().post("/api/upload_video", json={"video_path": "v.mp4", "title": "t"})
    assert response.status_code == 403


def test_upload_success(monkeypatch):
    monkeypatch.setattr(routes, "upload_video", lambda **kwargs: {"success": True, "video_id": "x1"})
    response = _client().post("/api/upload_video", json={"video_path": "v.mp4", "title": "t", "explicit_approval": True})
    assert response.json()["video_id"] == "x1"


def test_upload_generic_error_maps_to_400(monkeypatch):
    def boom(**kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(routes, "upload_video", boom)
    response = _client().post("/api/upload_video", json={"video_path": "v.mp4", "title": "t", "explicit_approval": True})
    assert response.status_code == 400


def test_super_pipeline_endpoint(monkeypatch):
    monkeypatch.setattr(routes, "generate_subtitles", lambda script, title="subtitles", audio_path=None: {"srt_path": "s.srt", "vtt_path": "s.vtt"})
    monkeypatch.setattr(routes, "create_video_from_script_and_audio", lambda **kwargs: {"video_path": "v.mp4"})

    async def fake_metadata(script, idea=None, language=None):
        return {"title": "Meta"}

    monkeypatch.setattr(routes, "generate_metadata", fake_metadata)
    monkeypatch.setattr(routes, "create_thumbnail", lambda title, output_name=None: Path("/tmp/t.jpg"))

    response = _client().post("/api/super_pipeline", json={"script": "guion", "title": "t"})
    body = response.json()
    assert body["success"] is True
    assert body["audio_path"] == "/tmp/fake_audio.mp3"
    assert body["youtube_configured"] is False


def test_agent_skills_endpoint():
    body = _client().get("/api/agent/skills").json()
    assert body["name"] == "ContentGremlin"
    assert "workflow" in body
