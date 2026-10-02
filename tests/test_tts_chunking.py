import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.config import settings
from providers.tts import TTSProvider


def test_split_text_respects_max_chars_without_sentence_breaks():
    text = " ".join(f"palabra{i}" for i in range(1200))
    chunks = TTSProvider()._split_text(text, max_chars=500)
    assert len(chunks) > 1
    assert all(len(c) <= 500 for c in chunks)
    assert " ".join(chunks).replace(".", " ").split() == text.split()


def test_split_text_keeps_short_text_single_chunk():
    assert TTSProvider()._split_text("texto corto", max_chars=500) == ["texto corto"]


def test_openai_tts_generates_every_chunk(monkeypatch, tmp_path):
    provider = TTSProvider()
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    long_text = " ".join(f"oracion numero {i} para la prueba" for i in range(600))
    assert len(long_text) > 4000

    calls = []

    async def fake_single(text, voice):
        calls.append((text, voice))
        return b"ID3fake"

    def fake_concat(parts, out_path):
        out_path.write_bytes(b"".join(p.read_bytes() for p in parts))

    monkeypatch.setattr(provider, "_openai_single", fake_single)
    monkeypatch.setattr(provider, "_concat_audio", fake_concat)

    out = tmp_path / "out.mp3"
    asyncio.run(provider._openai(long_text, out, "alloy"))

    assert len(calls) > 1
    assert all(len(chunk) <= 4000 for chunk, _ in calls)
    assert out.read_bytes() == b"ID3fake" * len(calls)


def test_openai_tts_single_chunk_skips_concat(monkeypatch, tmp_path):
    provider = TTSProvider()
    monkeypatch.setattr(settings, "openai_api_key", "test-key")

    async def fake_single(text, voice):
        return b"ID3single"

    def fail_concat(parts, out_path):
        raise AssertionError("concat must not be called for a single chunk")

    monkeypatch.setattr(provider, "_openai_single", fake_single)
    monkeypatch.setattr(provider, "_concat_audio", fail_concat)

    out = tmp_path / "single.mp3"
    asyncio.run(provider._openai("texto corto para narrar", out, "alloy"))
    assert out.read_bytes() == b"ID3single"


def test_elevenlabs_generates_every_chunk(monkeypatch, tmp_path):
    provider = TTSProvider()
    long_text = " ".join(f"oracion {i} de la prueba" for i in range(700))
    assert len(long_text) > 4500

    calls = []

    async def fake_single(text, voice_id):
        calls.append((text, voice_id))
        return b"ID3xi"

    def fake_concat(parts, out_path):
        out_path.write_bytes(b"".join(p.read_bytes() for p in parts))

    monkeypatch.setattr(provider, "_elevenlabs_single", fake_single)
    monkeypatch.setattr(provider, "_concat_audio", fake_concat)

    out = tmp_path / "xi.mp3"
    asyncio.run(provider._elevenlabs(long_text, out, None))

    assert len(calls) > 1
    assert all(len(chunk) <= 4500 for chunk, _ in calls)
    assert out.read_bytes() == b"ID3xi" * len(calls)


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe not installed",
)
def test_concat_audio_with_real_ffmpeg(tmp_path):
    provider = TTSProvider()
    parts = []
    for i, freq in enumerate((440, 660)):
        part = tmp_path / f"part_{i}.mp3"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency={freq}:duration=0.4", "-c:a", "libmp3lame", str(part)],
            capture_output=True, check=True,
        )
        parts.append(part)

    out = tmp_path / "joined.mp3"
    provider._concat_audio(parts, out)

    assert out.exists() and out.stat().st_size > 0
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(out)],
        capture_output=True, text=True,
    )
    duration = float(json.loads(probe.stdout)["format"]["duration"])
    assert duration >= 0.7
    assert not (tmp_path / ".joined_concat.txt").exists()
