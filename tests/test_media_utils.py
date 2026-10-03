import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import modules.subtitles as subs
from modules.video_creator import _escape_drawtext, _split_title_lines


def test_split_title_lines_breaks_long_titles():
    title = "Esta es una guia extensa de edicion para YouTube con muchas palabras"
    lines = _split_title_lines(title)
    assert 1 <= len(lines) <= 3
    assert all(len(line) <= 30 for line in lines)


def test_split_title_lines_handles_empty_title():
    assert _split_title_lines("") == [""]


def test_escape_drawtext():
    assert _escape_drawtext("Hola: mundo 'con' enter\n") == "Hola\\: mundo con enter"


def test_chunk_sentence_splits_long_text():
    chunks = subs._chunk_sentence(" ".join(f"palabra{i}" for i in range(60)), max_chars=40)
    assert len(chunks) > 1
    assert all(len(c) <= 40 for c in chunks)


def test_split_into_cues_without_duration_uses_word_rate():
    cues = subs._split_into_cues("Una frase corta. Otra frase un poco mas larga que la anterior.")
    assert cues[0]["start"] == 0.0
    assert cues[0]["end"] < cues[-1]["end"]
    assert all(c["start"] < c["end"] for c in cues)


def test_split_into_cues_spreads_across_total_duration():
    cues = subs._split_into_cues("Uno. Dos. Tres.", total_duration=30.0)
    assert cues[0]["start"] == 0.0
    assert cues[-1]["end"] >= 29.0


def test_time_formatters():
    assert subs._fmt_srt_time(3661.5) == "01:01:01,500"
    assert subs._fmt_vtt_time(3661.5) == "01:01:01.500"


def test_generate_subtitles_aligns_to_audio(monkeypatch, tmp_path):
    monkeypatch.setattr(subs, "SUB_DIR", tmp_path)
    monkeypatch.setattr(subs, "_probe_duration", lambda path: 10.0)

    result = subs.generate_subtitles("Primera. Segunda frase. Tercera.", "demo", audio_path=tmp_path / "x.mp3")

    srt = Path(result["srt_path"])
    vtt = Path(result["vtt_path"])
    assert result["aligned_to_audio"] is True
    assert srt.exists() and vtt.exists()
    assert "--> 00:00:10" in srt.read_text(encoding="utf-8")
    assert vtt.read_text(encoding="utf-8").startswith("WEBVTT")
