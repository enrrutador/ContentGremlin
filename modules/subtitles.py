"""
ContentGremlin - Subtitles
Generate SRT / VTT from script and optionally burn into video.
"""

from pathlib import Path
from typing import Optional
import re
from core.config import DATA_DIR

SUB_DIR = DATA_DIR / "subtitles"
SUB_DIR.mkdir(parents=True, exist_ok=True)


def _split_into_cues(text: str, max_chars: int = 80, words_per_minute: int = 150) -> list[dict]:
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    cues = []
    current_time = 0.0
    secs_per_word = 60.0 / words_per_minute

    for sentence in sentences:
        words = sentence.split()
        chunks = []
        buf = []
        for w in words:
            buf.append(w)
            if len(" ".join(buf)) >= max_chars:
                chunks.append(" ".join(buf))
                buf = []
        if buf:
            chunks.append(" ".join(buf))

        for chunk in chunks:
            duration = max(1.5, len(chunk.split()) * secs_per_word)
            cues.append({"start": current_time, "end": current_time + duration, "text": chunk})
            current_time += duration

    return cues


def _fmt_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _fmt_vtt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def generate_srt(script: str, title: str = "subtitles") -> Path:
    cues = _split_into_cues(script)
    safe = "".join(c for c in title if c.isalnum() or c in "-_")[:50] or "subtitles"
    path = SUB_DIR / f"{safe}.srt"
    lines = []
    for i, cue in enumerate(cues, 1):
        lines.append(str(i))
        lines.append(f"{_fmt_srt_time(cue['start'])} --> {_fmt_srt_time(cue['end'])}")
        lines.append(cue["text"])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_vtt(script: str, title: str = "subtitles") -> Path:
    cues = _split_into_cues(script)
    safe = "".join(c for c in title if c.isalnum() or c in "-_")[:50] or "subtitles"
    path = SUB_DIR / f"{safe}.vtt"
    lines = ["WEBVTT", ""]
    for cue in cues:
        lines.append(f"{_fmt_vtt_time(cue['start'])} --> {_fmt_vtt_time(cue['end'])}")
        lines.append(cue["text"])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_subtitles(script: str, title: str = "subtitles") -> dict:
    srt = generate_srt(script, title)
    vtt = generate_vtt(script, title)
    return {"srt_path": str(srt), "vtt_path": str(vtt), "format": ["srt", "vtt"]}
