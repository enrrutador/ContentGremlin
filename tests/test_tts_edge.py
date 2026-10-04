"""Edge-TTS gratis: routing, chunking y voz default. Sin red (mock edge_tts)."""

import asyncio
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.config import settings
from providers.tts import TTSProvider


def _fake_edge_tts(monkeypatch, calls):
    mod = types.ModuleType("edge_tts")

    class FakeCommunicate:
        def __init__(self, text, voice):
            calls.append((text, voice))

        async def save(self, path):
            Path(path).write_bytes(b"ID3edge")

    mod.Communicate = FakeCommunicate
    monkeypatch.setitem(sys.modules, "edge_tts", mod)
    return mod


def test_edge_generates_single_chunk(monkeypatch, tmp_path):
    calls = []
    _fake_edge_tts(monkeypatch, calls)
    provider = TTSProvider()
    out = tmp_path / "narr.mp3"
    asyncio.run(provider._edge("Hola mundo, esta es una prueba suficiente.", out, None))
    assert out.read_bytes() == b"ID3edge"
    assert calls and calls[0][1] == settings.edge_tts_voice


def test_edge_generates_every_chunk(monkeypatch, tmp_path):
    calls = []
    _fake_edge_tts(monkeypatch, calls)
    provider = TTSProvider()
    long_text = " ".join(f"oracion numero {i} para la prueba de voz" for i in range(600))
    assert len(long_text) > 4000

    def fake_concat(parts, out_path):
        out_path.write_bytes(b"".join(p.read_bytes() for p in parts))

    monkeypatch.setattr(provider, "_concat_audio", fake_concat)
    out = tmp_path / "largo.mp3"
    asyncio.run(provider._edge(long_text, out, "es-ES-AlvaroNeural"))
    assert len(calls) > 1
    assert all(v == "es-ES-AlvaroNeural" for _, v in calls)
    assert out.read_bytes() == b"ID3edge" * len(calls)


def test_generate_routes_to_edge_when_preferred(monkeypatch, tmp_path):
    import providers.tts as tts_mod

    monkeypatch.setattr(tts_mod, "AUDIO_DIR", tmp_path)
    monkeypatch.setattr(tts_mod, "load_user_profile", lambda: {"tts_provider": "edge"})
    calls = []
    _fake_edge_tts(monkeypatch, calls)
    provider = TTSProvider()
    assert provider.preferred == "edge"
    out = asyncio.run(provider.generate("Texto suficientemente largo para sintetizar.", filename="ep-edge"))
    assert out.read_bytes() == b"ID3edge"
    assert len(calls) == 1
