import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import api.routes as routes
from api.routes import SuperPipelineRequest, SubtitlesRequest


class FakeTTS:
    async def generate(self, text, filename=None, voice=None):
        return Path("/tmp/fake_audio.mp3")


def _patch_pipeline(monkeypatch, captured, tmp_path):
    def fake_generate_subtitles(script, title="subtitles", audio_path=None):
        captured["subtitles_audio_path"] = audio_path
        return {"srt_path": str(tmp_path / "sub.srt"), "vtt_path": str(tmp_path / "sub.vtt")}

    def fake_create_video(**kwargs):
        captured["video_audio_path"] = kwargs.get("audio_path")
        return {"video_path": str(tmp_path / "video.mp4")}

    async def fake_generate_metadata(script, idea=None, language=None):
        return {"title": "Meta"}

    def fake_create_thumbnail(title, output_name=None):
        return tmp_path / "thumb.jpg"

    def fake_add_item(**kwargs):
        return {"id": "lib-1"}

    monkeypatch.setattr(routes, "TTSProvider", FakeTTS)
    monkeypatch.setattr(routes, "generate_subtitles", fake_generate_subtitles)
    monkeypatch.setattr(routes, "create_video_from_script_and_audio", fake_create_video)
    monkeypatch.setattr(routes, "generate_metadata", fake_generate_metadata)
    monkeypatch.setattr(routes, "create_thumbnail", fake_create_thumbnail)
    monkeypatch.setattr(routes, "add_item", fake_add_item)
    monkeypatch.setattr(routes, "is_youtube_configured", lambda: False)


def test_super_pipeline_aligns_subtitles_to_generated_audio(monkeypatch, tmp_path):
    captured = {}
    _patch_pipeline(monkeypatch, captured, tmp_path)

    request = SuperPipelineRequest(script="guion de prueba", title="demo")
    result = asyncio.run(routes.api_super_pipeline(request))

    assert captured["subtitles_audio_path"] == Path("/tmp/fake_audio.mp3")
    assert captured["video_audio_path"] == Path("/tmp/fake_audio.mp3")
    assert result["success"] is True
    assert result["audio_path"] == "/tmp/fake_audio.mp3"


def test_generate_subtitles_endpoint_forwards_audio_path(monkeypatch, tmp_path):
    captured = {}

    def fake_generate_subtitles(script, title="subtitles", audio_path=None):
        captured["audio_path"] = audio_path
        return {"srt_path": "a.srt", "vtt_path": "a.vtt"}

    monkeypatch.setattr(routes, "generate_subtitles", fake_generate_subtitles)
    monkeypatch.setattr(routes, "add_item", lambda **kwargs: {"id": "x"})

    audio = str(tmp_path / "voice.mp3")
    request = SubtitlesRequest(script="hola mundo", title="demo", audio_path=audio)
    asyncio.run(routes.api_generate_subtitles(request))

    assert captured["audio_path"] == audio
