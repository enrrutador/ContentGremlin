import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import modules.thumbnail as thumbnails
import modules.video_creator as video_creator

FFMPEG_AVAILABLE = shutil.which("ffmpeg") and shutil.which("ffprobe")
pytestmark = pytest.mark.skipif(not FFMPEG_AVAILABLE, reason="ffmpeg/ffprobe not installed")


def _tone_mp3(path, duration=1.0):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}", "-c:a", "libmp3lame", str(path)],
        capture_output=True, check=True,
    )
    return path


def _probe_duration(path):
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True, text=True,
    )
    return float(json.loads(probe.stdout)["format"]["duration"])


def test_create_simple_video_with_real_audio(monkeypatch, tmp_path):
    monkeypatch.setattr(video_creator, "VIDEO_DIR", tmp_path)
    audio = _tone_mp3(tmp_path / "tone.mp3")

    out = video_creator.create_simple_video(
        audio_path=audio, title="Video de prueba", output_name="test", resolution="640x360"
    )

    assert out.exists() and out.stat().st_size > 0
    assert 0.8 <= _probe_duration(out) <= 1.6


def test_create_video_from_script_and_audio_returns_metadata(monkeypatch, tmp_path):
    monkeypatch.setattr(video_creator, "VIDEO_DIR", tmp_path)
    audio = _tone_mp3(tmp_path / "tone.mp3")

    result = video_creator.create_video_from_script_and_audio(
        script="", audio_path=audio, title="Titulo", output_name="t2", template="studio_blue"
    )

    assert Path(result["video_path"]).exists()
    assert result["title"] == "Titulo"
    assert result["template"] == "studio_blue"
    assert result["size_bytes"] > 0


def test_burn_subtitles_into_video(monkeypatch, tmp_path):
    monkeypatch.setattr(video_creator, "VIDEO_DIR", tmp_path)
    audio = _tone_mp3(tmp_path / "tone.mp3")
    video = video_creator.create_simple_video(audio_path=audio, title="Subs", output_name="subtest")

    srt = tmp_path / "s.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:00,800\nHola mundo\n", encoding="utf-8")

    burned = video_creator.burn_subtitles(video, srt, output_name="burned")
    assert burned.exists() and burned.stat().st_size > 0


def test_thumbnail_is_a_jpeg(monkeypatch, tmp_path):
    monkeypatch.setattr(thumbnails, "THUMB_DIR", tmp_path)

    out = thumbnails.create_thumbnail("Mi primer video: guia completa", output_name="thumb1")

    assert out.read_bytes()[:2] == b"\xff\xd8"
