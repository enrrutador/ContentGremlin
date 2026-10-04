"""Cobertura de producción con ffmpeg real (pequeño y rápido) + puros sin red."""

import asyncio
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import modules.audio_mix as am
import modules.broll as broll
import modules.production_engine as pe
import modules.qa_agent as qa

ffmpeg = shutil.which("ffmpeg")
needs_ffmpeg = pytest.mark.skipif(not ffmpeg, reason="ffmpeg no disponible")


def _tone(out: Path, seconds: float = 1.0) -> Path:
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
         "-c:a", "libmp3lame", str(out)],
        capture_output=True, timeout=60, check=True,
    )
    return out


def test_broll_keywords_and_scoring():
    assert "cocina" in broll._keywords("Recetas de cocina fácil y ahorro")
    assert broll._keywords("the and for") == "cinematic abstract"
    good = {"width": 1920, "height": 1080, "duration": 5}
    bad = {"width": 320, "height": 240, "duration": 60}
    assert broll._score_video_file(good, target_duration=5, prefer_hd=True, prefer_vertical=False) > \
        broll._score_video_file(bad, target_duration=5, prefer_hd=True, prefer_vertical=False)


def test_production_parse_resolution():
    assert pe._parse_resolution("1280x720") == (1280, 720)
    assert pe._parse_resolution("basura") == (1920, 1080)


def test_audio_mix_library_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(am, "MUSIC_DIR", tmp_path)
    assert am.list_music_tracks() == []
    assert am.pick_music_track() is None
    st = am.music_library_status()
    assert st["track_count"] == 0


@needs_ffmpeg
def test_still_trim_concat_real(tmp_path, monkeypatch):
    monkeypatch.setattr(pe, "WORK_DIR", tmp_path)
    monkeypatch.setattr(pe, "OUT_DIR", tmp_path)
    s1 = pe._still_clip(1.0, tmp_path / "s1.mp4", 320, 240, 15)
    s2 = pe._still_clip(1.0, tmp_path / "s2.mp4", 320, 240, 15)
    assert s1.exists() and s2.exists()
    t = pe._trim_clip(s1, 1.0, tmp_path / "t.mp4", 320, 240, 15)
    assert t.exists()
    out = pe._concat_clips([s1, s2], tmp_path / "cat.mp4")
    assert out.exists() and out.stat().st_size > 1000
    with pytest.raises(ValueError):
        pe._concat_clips([], tmp_path / "vacio.mp4")


@needs_ffmpeg
def test_qa_scores_real_clip(tmp_path, monkeypatch):
    monkeypatch.setattr(pe, "WORK_DIR", tmp_path)
    clip = pe._still_clip(2.0, tmp_path / "qa.mp4", 320, 240, 15)
    out = qa.run_qa(clip, prod={"quality_bar": "draft", "min_duration_seconds": 1, "max_duration_seconds": 1200})
    assert out["checks"]["exists"] is True
    assert isinstance(out["score"], float)
    assert "threshold" in out and "reasons" in out
    # clip de juguete 320x240: la QA debe encontrar motivos (resolución/tamaño)
    assert out["checks"]["duration_seconds"] >= 1.5


@needs_ffmpeg
def test_audio_probe_and_music_pick(tmp_path, monkeypatch):
    tone = _tone(tmp_path / "m.mp3", 1.0)
    assert am._probe_duration(tone) > 0.5
    monkeypatch.setattr(am, "MUSIC_DIR", tmp_path)
    assert am.pick_music_track() is not None


@needs_ffmpeg
def test_produce_still_style_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(pe, "WORK_DIR", tmp_path / "work")
    monkeypatch.setattr(pe, "OUT_DIR", tmp_path / "out")
    (tmp_path / "out").mkdir()

    class FakeTTS:
        async def generate(self, text, filename=None, voice=None):
            return _tone(tmp_path / "narr.mp3", 2.0)

    scenes = [
        {"index": 1, "narration_excerpt": "hola", "duration_seconds": 2.0,
         "visual_prompt": "kitchen", "motion": "static", "mood": "neutral"},
        {"index": 2, "narration_excerpt": "mundo", "duration_seconds": 2.0,
         "visual_prompt": "garden", "motion": "static", "mood": "neutral"},
    ]

    async def fake_scenes(**kwargs):
        return scenes

    monkeypatch.setattr(pe, "TTSProvider", FakeTTS)
    monkeypatch.setattr(pe, "plan_scenes", fake_scenes)
    monkeypatch.setattr(
        pe, "get_production_config",
        lambda: {"visual_style": "still", "editing_pace": "medium", "subtitle_style": "none",
                 "target_resolution": "320x240", "fps": 15, "transition": "none",
                 "music": {"enabled": False}, "quality_bar": "draft",
                 "min_duration_seconds": 1, "max_duration_seconds": 1200},
    )

    script = "Esta es una prueba de producción con suficientes palabras para pasar la validación mínima. " * 4
    out = asyncio.run(pe.produce(script=script, title="ep-test", skip_qa=False))
    assert out["success"] is True
    assert Path(out["video_path"]).exists()
    assert out["qa"]["checks"]["exists"] is True


@needs_ffmpeg
def test_broll_fetch_uses_cache_and_marks_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(broll, "CACHE_DIR", tmp_path)

    async def fake_clip(query, target_duration=5, source="mixed", prefer_hd=True, prefer_vertical=False):
        if "vacio" in query:
            return None
        p = tmp_path / "stock.mp4"
        if not p.exists():
            subprocess.run(
                ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=1",
                 "-c:v", "libx264", "-pix_fmt", "yuv420p", str(p)],
                capture_output=True, timeout=60, check=True,
            )
        return {"path": str(p), "query": query, "provider": "test", "duration": target_duration, "score": 1.0}

    monkeypatch.setattr(broll, "fetch_clip_for_query", fake_clip)
    scenes = [
        {"index": 1, "visual_prompt": "cocina", "narration_excerpt": "x", "duration_seconds": 3.0},
        {"index": 2, "visual_prompt": "vacio total", "narration_excerpt": "y", "duration_seconds": 3.0},
    ]
    out = asyncio.run(broll.fetch_broll_for_scenes(scenes, {"source": "mixed"}))
    assert len(out) == 2
    assert out[0]["type"] == "stock"
    assert out[1]["type"] == "missing"


@needs_ffmpeg
def test_music_mix_real(tmp_path, monkeypatch):
    monkeypatch.setattr(am, "MUSIC_DIR", tmp_path)
    monkeypatch.setattr(am, "WORK_DIR", tmp_path)
    music = _tone(tmp_path / "bg.mp3", 2.0)
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=red:s=320x240:d=2",
         "-f", "lavfi", "-i", "sine=frequency=220:duration=2",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
         str(tmp_path / "v.mp4")],
        capture_output=True, timeout=60, check=True,
    )
    out = am.mix_music_under_video(tmp_path / "v.mp4", music_path=music, output_name="mix")
    assert Path(out).exists() and Path(out).stat().st_size > 1000


@needs_ffmpeg
def test_cinematic_clip_chain_real(tmp_path):
    import modules.cinematic as cine

    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=green:s=320x240:d=1",
         "-frames:v", "1", str(tmp_path / "img.png")],
        capture_output=True, timeout=60, check=True,
    )
    c1 = cine._image_to_clip(tmp_path / "img.png", 1.0, "static", tmp_path / "c1.mp4")
    c2 = cine._image_to_clip(tmp_path / "img.png", 1.0, "slow_zoom_in", tmp_path / "c2.mp4")
    assert c1.exists() and c2.exists()
    silent = cine._concat_clips([c1, c2], tmp_path / "silent.mp4")
    assert silent.exists()
    tone = _tone(tmp_path / "a.mp3", 2.0)
    final = cine._mux_audio(silent, tone, tmp_path / "final.mp4")
    assert final.exists() and final.stat().st_size > 1000
    assert cine._probe_duration(final) >= 1.5


@needs_ffmpeg
def test_qa_audio_measurements_real(tmp_path):
    tone = _tone(tmp_path / "t.mp3", 2.0)
    assert qa._mean_volume_db(tone) is not None
    assert qa._max_silence_seconds(tone) is not None
    assert qa._audio_energy_in_window(tone, 0.0, 1.0) is not None


def test_uploader_retryable_matrix():
    import modules.uploader as up

    class FakeResp:
        def __init__(self, status):
            self.status = status

    class FakeErr(Exception):
        def __init__(self, status=None):
            self.resp = FakeResp(status) if status else None

    assert up._is_retryable(FakeErr(500)) is True
    assert up._is_retryable(FakeErr(404)) is False
    assert up._is_retryable(ConnectionError("x")) is True

    class TransportError(Exception):
        pass

    assert up._is_retryable(TransportError("y")) is True


def test_resolve_visuals_still_needs_no_network():
    scenes = [{"index": 1, "visual_prompt": "x", "duration_seconds": 3.0}]
    out = asyncio.run(pe._resolve_visuals(scenes, {"visual_style": "still", "broll": {"enabled": False}}))
    assert out[0]["type"] == "still"


@needs_ffmpeg
def test_cinematic_full_pipeline_mocked_network(tmp_path, monkeypatch):
    import modules.cinematic as cine
    import modules.scene_planner as planner

    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=navy:s=320x240:d=1",
         "-frames:v", "1", str(tmp_path / "frame.png")],
        capture_output=True, timeout=60, check=True,
    )

    class FakeTTS:
        async def generate(self, text, filename=None, voice=None):
            return _tone(tmp_path / "narr.mp3", 3.0)

    async def fake_scenes(**kwargs):
        return [
            {"index": 1, "narration_excerpt": "a", "duration_seconds": 1.5,
             "visual_prompt": "kitchen dawn", "motion": "static", "mood": "calm"},
            {"index": 2, "narration_excerpt": "b", "duration_seconds": 1.5,
             "visual_prompt": "garden dusk", "motion": "static", "mood": "calm"},
        ]

    class FakeImg:
        provider = "test"
        def is_configured(self):
            return True

        async def generate(self, prompt, filename=None):
            return tmp_path / "frame.png"

    class FakeVideoGen:
        provider = "none"
        def is_configured(self):
            return False

    monkeypatch.setattr(cine, "TTSProvider", FakeTTS)
    monkeypatch.setattr(cine, "plan_scenes", fake_scenes)
    monkeypatch.setattr(cine, "ImageProvider", FakeImg)
    monkeypatch.setattr(cine, "VideoGenProvider", FakeVideoGen)
    monkeypatch.setattr(cine, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(cine, "OUT_DIR", tmp_path / "out")
    (tmp_path / "scenes").mkdir()
    (tmp_path / "out").mkdir()

    out = asyncio.run(cine.create_cinematic_video(script="hola mundo " * 30, title="cin-test"))
    assert Path(out["video_path"]).exists()
    assert out["mode"] == "cinematic"
    assert len(out["scenes"]) == 2
    assert out["scenes"][0]["source"] == "image_kenburns"


def test_broll_falls_back_from_pexels_to_pixabay(monkeypatch):
    async def no_pexels(*a, **k):
        return None

    async def yes_pixabay(*a, **k):
        return {"path": "/tmp/x.mp4", "query": "q", "provider": "pixabay",
                "duration": 5, "score": 9.0}

    monkeypatch.setattr(broll, "_pexels_search", no_pexels)
    monkeypatch.setattr(broll, "_pixabay_search", yes_pixabay)
    clip = asyncio.run(broll.fetch_clip_for_query("cocina", source="mixed"))
    assert clip["provider"] == "pixabay"

    async def yes_pexels(*a, **k):
        return {"path": "/tmp/y.mp4", "query": "q", "provider": "pexels",
                "duration": 5, "score": 9.0}

    monkeypatch.setattr(broll, "_pexels_search", yes_pexels)
    clip = asyncio.run(broll.fetch_clip_for_query("cocina", source="pexels"))
    assert clip["provider"] == "pexels"
    assert broll.broll_status()["pexels_configured"] is False


@needs_ffmpeg
def test_produce_hybrid_crossfade_music_burn(tmp_path, monkeypatch):
    import modules.broll as broll_mod
    import modules.audio_mix as am_mod

    monkeypatch.setattr(pe, "WORK_DIR", tmp_path / "work")
    monkeypatch.setattr(pe, "OUT_DIR", tmp_path / "out")
    (tmp_path / "out").mkdir()
    monkeypatch.setattr(am_mod, "MUSIC_DIR", tmp_path / "music")
    (tmp_path / "music").mkdir()
    _tone(tmp_path / "music" / "bg.mp3", 4.0)
    stock = pe._still_clip(3.0, tmp_path / "stock.mp4", 320, 240, 15)

    class FakeTTS:
        async def generate(self, text, filename=None, voice=None):
            return _tone(tmp_path / "narr.mp3", 4.0)

    async def fake_scenes(**kwargs):
        return [
            {"index": 1, "narration_excerpt": "a", "duration_seconds": 2.0,
             "visual_prompt": "kitchen", "motion": "static", "mood": "calm"},
            {"index": 2, "narration_excerpt": "b", "duration_seconds": 2.0,
             "visual_prompt": "garden", "motion": "static", "mood": "calm"},
        ]

    async def fake_broll(scenes, cfg):
        return [{"scene_index": s["index"], "type": "stock", "query": "q",
                 "clip_path": str(stock), "provider": "test",
                 "duration_seconds": 3.0, "source_duration": 3.0, "score": 9.0}
                for s in scenes]

    monkeypatch.setattr(pe, "TTSProvider", FakeTTS)
    monkeypatch.setattr(pe, "plan_scenes", fake_scenes)
    monkeypatch.setattr(broll_mod, "fetch_broll_for_scenes", fake_broll)
    monkeypatch.setattr(
        pe, "get_production_config",
        lambda: {"visual_style": "hybrid", "editing_pace": "fast", "subtitle_style": "minimal",
                 "target_resolution": "320x240", "fps": 15, "transition": "crossfade",
                 "transition_duration": 0.5,
                 "music": {"enabled": True, "intensity": 0.2, "duck_strength": 0.6,
                           "mood": "auto", "intro_fade_seconds": 0.5, "outro_fade_seconds": 0.5},
                 "quality_bar": "draft",
                 "min_duration_seconds": 1, "max_duration_seconds": 1200},
    )

    script = "Palabra de relleno para el guion de prueba. " * 12
    out = asyncio.run(pe.produce(script=script, title="ep-hybrid", skip_qa=False))
    assert out["success"] is True
    assert Path(out["video_path"]).exists()
    assert out["music"]["applied"] is True
    assert out["qa"]["checks"]["exists"] is True
