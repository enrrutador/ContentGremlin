"""ContentGremlin - Subtitles with optional audio-duration alignment."""
from __future__ import annotations
from pathlib import Path
from typing import Optional
import re, json, subprocess
from core.config import DATA_DIR

SUB_DIR = DATA_DIR / "subtitles"
SUB_DIR.mkdir(parents=True, exist_ok=True)

def _probe_duration(path: Path) -> Optional[float]:
    try:
        probe = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)], capture_output=True, text=True, timeout=30)
        return float(json.loads(probe.stdout)["format"]["duration"])
    except Exception:
        return None

def _sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]

def _chunk_sentence(sentence: str, max_chars: int = 72) -> list[str]:
    words, chunks, buf = sentence.split(), [], []
    for w in words:
        trial = (" ".join(buf + [w])).strip()
        if len(trial) <= max_chars: buf.append(w)
        else:
            if buf: chunks.append(" ".join(buf))
            buf = [w]
    if buf: chunks.append(" ".join(buf))
    return chunks or [sentence]

def _split_into_cues(text: str, total_duration: Optional[float] = None, max_chars: int = 72, words_per_minute: int = 150) -> list[dict]:
    chunks: list[str] = []
    for s in _sentences(text):
        chunks.extend(_chunk_sentence(s, max_chars=max_chars))
    if not chunks:
        return [{"start": 0.0, "end": 2.0, "text": text[:72] or "..."}]
    weights = [max(1, len(c.split())) for c in chunks]
    total_weight = sum(weights)
    if total_duration and total_duration > 1:
        cues, t = [], 0.0
        for chunk, w in zip(chunks, weights):
            dur = max(1.2, total_duration * (w / total_weight))
            end = min(total_duration, t + dur)
            if end <= t: end = t + 1.0
            cues.append({"start": t, "end": end, "text": chunk})
            t = end
        if cues: cues[-1]["end"] = max(cues[-1]["end"], total_duration)
        return cues
    secs_per_word = 60.0 / words_per_minute
    cues, t = [], 0.0
    for chunk, w in zip(chunks, weights):
        dur = max(1.5, w * secs_per_word)
        cues.append({"start": t, "end": t + dur, "text": chunk})
        t += dur
    return cues

def _fmt_srt_time(seconds: float) -> str:
    h, m = int(seconds // 3600), int((seconds % 3600) // 60)
    s, ms = int(seconds % 60), int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000: ms = 999
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def _fmt_vtt_time(seconds: float) -> str:
    h, m = int(seconds // 3600), int((seconds % 3600) // 60)
    s, ms = int(seconds % 60), int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000: ms = 999
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def generate_srt(script: str, title: str = "subtitles", audio_path: Optional[str | Path] = None) -> Path:
    duration = _probe_duration(Path(audio_path)) if audio_path else None
    cues = _split_into_cues(script, total_duration=duration)
    safe = "".join(c for c in title if c.isalnum() or c in "-_")[:50] or "subtitles"
    path = SUB_DIR / f"{safe}.srt"
    lines = []
    for i, cue in enumerate(cues, 1):
        lines += [str(i), f"{_fmt_srt_time(cue['start'])} --> {_fmt_srt_time(cue['end'])}", cue["text"], ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

def generate_vtt(script: str, title: str = "subtitles", audio_path: Optional[str | Path] = None) -> Path:
    duration = _probe_duration(Path(audio_path)) if audio_path else None
    cues = _split_into_cues(script, total_duration=duration)
    safe = "".join(c for c in title if c.isalnum() or c in "-_")[:50] or "subtitles"
    path = SUB_DIR / f"{safe}.vtt"
    lines = ["WEBVTT", ""]
    for cue in cues:
        lines += [f"{_fmt_vtt_time(cue['start'])} --> {_fmt_vtt_time(cue['end'])}", cue["text"], ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

def generate_subtitles(script: str, title: str = "subtitles", audio_path: Optional[str | Path] = None) -> dict:
    srt = generate_srt(script, title, audio_path=audio_path)
    vtt = generate_vtt(script, title, audio_path=audio_path)
    return {"srt_path": str(srt), "vtt_path": str(vtt), "format": ["srt", "vtt"], "aligned_to_audio": bool(audio_path)}
