"""
ContentGremlin - QA Agent
Technical + perceptual gates before a video is marked publishable.
Uses ffprobe / ffmpeg silencedetect + volumedetect. No LLM required.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Optional

from core.config import get_production_config
from core.storage import get_dir

QA_DIR = get_dir("qa")


def _ffprobe_json(path: Path) -> dict:
    r = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", str(path),
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    try:
        return json.loads(r.stdout or "{}")
    except Exception:
        return {}


def _probe_duration(path: Path) -> float:
    data = _ffprobe_json(path)
    try:
        return float(data.get("format", {}).get("duration") or 0)
    except Exception:
        return 0.0


def _probe_resolution(path: Path) -> tuple[int, int]:
    data = _ffprobe_json(path)
    for s in data.get("streams") or []:
        if s.get("codec_type") == "video":
            return int(s.get("width") or 0), int(s.get("height") or 0)
    return 0, 0


def _has_audio_stream(path: Path) -> bool:
    data = _ffprobe_json(path)
    return any(s.get("codec_type") == "audio" for s in (data.get("streams") or []))


def _max_silence_seconds(path: Path, noise_db: float = -35.0, min_sil: float = 0.4) -> float:
    """Return longest silence in seconds (0 if none / no audio)."""
    if not _has_audio_stream(path):
        return 999.0
    cmd = [
        "ffmpeg", "-i", str(path),
        "-af", f"silencedetect=noise={noise_db}dB:d={min_sil}",
        "-f", "null", "-",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    text = (r.stderr or "") + (r.stdout or "")
    starts = [float(x) for x in re.findall(r"silence_start:\s*([0-9.]+)", text)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([0-9.]+)", text)]
    if not starts:
        return 0.0
    longest = 0.0
    for i, st in enumerate(starts):
        en = ends[i] if i < len(ends) else _probe_duration(path)
        longest = max(longest, max(0.0, en - st))
    return longest


def _mean_volume_db(path: Path) -> Optional[float]:
    if not _has_audio_stream(path):
        return None
    cmd = ["ffmpeg", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    text = (r.stderr or "") + (r.stdout or "")
    m = re.search(r"mean_volume:\s*([\-0-9.]+)\s*dB", text)
    if m:
        return float(m.group(1))
    return None


def _audio_energy_in_window(path: Path, start: float, end: float) -> Optional[float]:
    """Mean volume (dB) in [start, end]. Higher (closer to 0) = louder."""
    if not _has_audio_stream(path):
        return None
    dur = max(0.1, end - start)
    cmd = [
        "ffmpeg", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}",
        "-i", str(path), "-af", "volumedetect", "-f", "null", "-",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    text = (r.stderr or "") + (r.stdout or "")
    m = re.search(r"mean_volume:\s*([\-0-9.]+)\s*dB", text)
    if m:
        return float(m.group(1))
    return None


def run_qa(
    video_path: str | Path,
    *,
    audio_path: str | Path | None = None,
    script: str | None = None,
    prod: dict | None = None,
) -> dict[str, Any]:
    """
    Evaluate whether a video meets the configured quality bar.

    Returns:
      ok, score (0-1), publishable, checks{}, reasons[], quality_bar, threshold
    """
    prod = prod or get_production_config()
    path = Path(video_path)
    checks: dict[str, Any] = {}
    reasons: list[str] = []
    score = 1.0

    quality_bar = prod.get("quality_bar", "publishable")
    thresholds = {"draft": 0.40, "review": 0.60, "publishable": 0.78}
    threshold = thresholds.get(quality_bar, 0.78)

    if not path.exists():
        return {
            "ok": False,
            "score": 0.0,
            "publishable": False,
            "checks": {"exists": False},
            "reasons": ["video_file_missing"],
            "quality_bar": quality_bar,
            "threshold": threshold,
        }

    checks["exists"] = True
    size = path.stat().st_size
    checks["size_bytes"] = size
    if size < 80_000:
        reasons.append("file_too_small")
        score -= 0.45

    duration = _probe_duration(path)
    checks["duration_seconds"] = round(duration, 2)
    min_d = float(prod.get("min_duration_seconds", 45))
    max_d = float(prod.get("max_duration_seconds", 1200))
    if duration < min_d:
        reasons.append(f"too_short ({duration:.1f}s < {min_d}s)")
        score -= 0.35
    if duration > max_d:
        reasons.append(f"too_long ({duration:.1f}s > {max_d}s)")
        score -= 0.12

    w, h = _probe_resolution(path)
    checks["resolution"] = f"{w}x{h}"
    checks["width"] = w
    checks["height"] = h
    if w < 640 or h < 360:
        reasons.append("resolution_too_low")
        score -= 0.30
    elif w < 1280 or h < 720:
        reasons.append("resolution_below_hd")
        score -= 0.08

    has_audio = _has_audio_stream(path)
    checks["has_audio"] = has_audio
    if not has_audio:
        reasons.append("no_audio_stream")
        score -= 0.50

    silence = _max_silence_seconds(path) if has_audio else 999.0
    checks["max_silence_seconds"] = round(silence, 2)
    sil_limit = float(prod.get("max_silence_seconds", 1.2))
    if silence > sil_limit:
        reasons.append(f"long_silence ({silence:.1f}s > {sil_limit}s)")
        score -= 0.22

    mean_db = _mean_volume_db(path) if has_audio else None
    checks["mean_volume_db"] = mean_db
    if mean_db is not None:
        if mean_db < -45:
            reasons.append("audio_too_quiet")
            score -= 0.20
        elif mean_db > -5:
            reasons.append("audio_possible_clipping")
            score -= 0.10

    hook_max = float(prod.get("hook_max_seconds", 3.0))
    hook_db = _audio_energy_in_window(path, 0.0, hook_max) if has_audio else None
    checks["hook_mean_volume_db"] = hook_db
    checks["hook_window_seconds"] = hook_max
    if hook_db is not None and hook_db < -42:
        reasons.append("weak_hook_low_energy")
        score -= 0.28
    elif hook_db is None and has_audio:
        reasons.append("hook_energy_unmeasured")
        score -= 0.05

    if script and len(script.strip()) < 80:
        reasons.append("script_too_short")
        score -= 0.15
        checks["script_chars"] = len(script.strip())
    elif script:
        checks["script_chars"] = len(script.strip())

    score = max(0.0, min(1.0, score))
    # hard blockers for publishable
    hard_fail = any(
        r.startswith(x)
        for r in reasons
        for x in ("video_file_missing", "no_audio_stream", "file_too_small", "too_short", "resolution_too_low")
    )
    ok = score >= threshold and not hard_fail
    if quality_bar == "draft":
        ok = score >= threshold and path.exists()

    result = {
        "ok": ok,
        "score": round(score, 3),
        "publishable": ok and quality_bar == "publishable",
        "checks": checks,
        "reasons": reasons,
        "quality_bar": quality_bar,
        "threshold": threshold,
    }

    # persist last QA report
    try:
        report_path = QA_DIR / f"qa_{path.stem}.json"
        report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        result["report_path"] = str(report_path)
    except Exception:
        pass

    return result
