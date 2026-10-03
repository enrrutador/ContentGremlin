import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import modules.analyzer as analyzer
from core.safety import SafetyError

FAKE = {
    "channel": "Canal de Prueba",
    "entries": [
        {"title": "7 formas de mejorar tu edicion", "view_count": 1000, "duration": 300, "id": "a", "url": "u1"},
        {"title": "¿Por qué nadie ve tus videos?", "view_count": 5000, "duration": 120, "id": "b", "url": "u2"},
        {"title": "Como ganar suscriptores en 2026", "view_count": 200, "duration": 30, "id": "c", "url": "u3"},
    ],
}


def test_title_formula_classification():
    assert analyzer._classify_title_formula("7 formas de crecer") == "listicle_number"
    assert analyzer._classify_title_formula("5 errores comunes al editar") == "listicle_number"
    assert analyzer._classify_title_formula("¿Por qué nadie te ve?") == "question"
    assert analyzer._classify_title_formula("Cómo editar rápido") == "howto"
    assert analyzer._classify_title_formula("iPhone vs Android") == "versus"
    assert analyzer._classify_title_formula("Lo mejor del 2026") == "year_bait"
    assert analyzer._classify_title_formula("Corto") == "short_punchy"
    assert analyzer._classify_title_formula("Una historia larga sobre producción de video") == "statement"


def test_duration_buckets():
    assert analyzer._duration_bucket(0) == "unknown"
    assert analyzer._duration_bucket(30) == "shorts_under_1m"
    assert analyzer._duration_bucket(120) == "short_1_3m"
    assert analyzer._duration_bucket(300) == "mid_3_8m"
    assert analyzer._duration_bucket(600) == "long_8_15m"
    assert analyzer._duration_bucket(1200) == "deep_15m_plus"


def test_hook_styles_detection():
    hooks = analyzer._hook_style_from_titles(["¿Qué pasa?", "El secreto de YouTube", "Yo gane 2026"])
    for expected in ("questions_in_title", "curiosity_gap", "first_person", "numbers"):
        assert expected in hooks


def test_hook_styles_default_to_plain_statement():
    assert analyzer._hook_style_from_titles(["Una historia comun"]) == ["plain_statement"]


def test_validate_analysis_request_rejects_empty():
    with pytest.raises(SafetyError):
        analyzer.validate_analysis_request("   ")


def test_analyze_channel_builds_patterns(monkeypatch):
    monkeypatch.setattr(analyzer, "_run_yt_dlp", lambda url: FAKE)
    report = analyzer.analyze_channel("MiCanal")
    assert report["channel_url"] == "https://www.youtube.com/@MiCanal"
    assert report["channel_name"] == "Canal de Prueba"
    assert report["videos_analyzed"] == 3
    patterns = report["patterns"]
    assert patterns["avg_duration_seconds"] == 150.0
    assert patterns["length_distribution"] == {"mid_3_8m": 1, "short_1_3m": 1, "shorts_under_1m": 1}
    assert patterns["dominant_length_bucket"] in {"mid_3_8m", "short_1_3m", "shorts_under_1m"}
    assert report["top_titles"][0] == "¿Por qué nadie ve tus videos?"
    assert report["reference_titles_for_safety"]


def test_analyze_channel_normalizes_handle(monkeypatch):
    captured = {}

    def fake_run(url):
        captured["url"] = url
        return FAKE

    monkeypatch.setattr(analyzer, "_run_yt_dlp", fake_run)
    analyzer.analyze_channel("@otro")
    assert captured["url"] == "https://www.youtube.com/@otro"


def test_analyze_channel_keeps_full_youtube_url(monkeypatch):
    captured = {}

    def fake_run(url):
        captured["url"] = url
        return FAKE

    monkeypatch.setattr(analyzer, "_run_yt_dlp", fake_run)
    analyzer.analyze_channel("https://www.youtube.com/@x")
    assert captured["url"] == "https://www.youtube.com/@x"


def test_run_yt_dlp_falls_back_to_second_command(monkeypatch):
    calls = []

    class Result:
        def __init__(self, returncode, stdout):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = "err"

    def fake_subprocess_run(cmd, capture_output=True, text=True, timeout=0):
        calls.append(cmd)
        if len(calls) == 1:
            return Result(1, "")
        return Result(0, '{"id": "x", "title": "T"}')

    monkeypatch.setattr(analyzer.subprocess, "run", fake_subprocess_run)
    data = analyzer._run_yt_dlp("https://www.youtube.com/@x")
    assert data["id"] == "x"
    assert len(calls) == 2
