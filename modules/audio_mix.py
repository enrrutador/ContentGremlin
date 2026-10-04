"""
ContentGremlin - Audio mix
Background music under narration with soft ducking (FFmpeg sidechain/volume).
"""
from __future__ import annotations

import random
import subprocess
from pathlib import Path
from typing import Any, Optional

from core.config import settings
from core.storage import get_dir

MUSIC_DIR = get_dir("music")
WORK_DIR = get_dir("production_work")


def _run(cmd: list[str], timeout: int = 600) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"FFmpeg audio mix error: {(r.stderr or '')[:1200]}")


def _probe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    try:
        import json

        return float(__import__("json").loads(r.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def list_music_tracks(mood: str = "auto") -> list[Path]:
    """Scan configured music library + data/music for audio files."""
    roots = [MUSIC_DIR]
    extra = Path(settings.music_library_dir)
    if extra.exists() and extra.resolve() != MUSIC_DIR.resolve():
        roots.append(extra)

    tracks: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for ext in ("*.mp3", "*.wav", "*.m4a", "*.ogg"):
            tracks.extend(root.glob(ext))
            tracks.extend(root.glob(f"**/{ext}"))

    # optional mood subfolders: data/music/upbeat/, etc.
    if mood and mood not in ("auto", "none"):
        mood_tracks = [t for t in tracks if mood.lower() in str(t).lower()]
        if mood_tracks:
            return mood_tracks
    return tracks


def pick_music_track(mood: str = "auto") -> Optional[Path]:
    tracks = list_music_tracks(mood)
    if not tracks:
        tracks = list_music_tracks("auto")
    if not tracks:
        return None
    return random.choice(tracks)


def mix_music_under_video(
    video_path: Path,
    *,
    music_path: Optional[Path] = None,
    intensity: float = 0.22,
    duck_strength: float = 0.65,
    mood: str = "auto",
    intro_fade: float = 1.5,
    outro_fade: float = 2.0,
    output_name: Optional[str] = None,
) -> Path:
    """
    Mix background music under existing video audio.
    Uses volume envelope: music starts at intensity, ducks when voice is present
    via a simplified dual-input amix (voice priority).
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    track = Path(music_path) if music_path else pick_music_track(mood)
    if not track or not track.exists():
        # no music available — return original
        return video_path

    intensity = max(0.0, min(1.0, intensity))
    duck = max(0.0, min(1.0, duck_strength))
    # ducked level when voice present
    ducked = intensity * (1.0 - duck * 0.85)

    dur = _probe_duration(video_path) or 60.0
    safe = "".join(c for c in (output_name or video_path.stem + "_music") if c.isalnum() or c in "-_")[:50]
    out = get_dir("videos") / f"{safe}.mp4"

    # Build filter:
    # - loop/trim music to video duration
    # - fade in/out
    # - sidechaincompress if available; fallback to constant low volume
    af = (
        f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{dur:.3f},"
        f"afade=t=in:st=0:d={intro_fade:.2f},"
        f"afade=t=out:st={max(0.0, dur - outro_fade):.3f}:d={outro_fade:.2f},"
        f"volume={intensity:.3f}[music];"
        f"[0:a]asplit=2[voice][sc];"
        f"[music][sc]sidechaincompress=threshold=0.08:ratio=6:attack=50:release=300:level_sc=1[ducked];"
        f"[voice][ducked]amix=inputs=2:duration=first:dropout_transition=0[aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(track),
        "-filter_complex", af,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(out),
    ]
    try:
        _run(cmd)
        return out
    except RuntimeError:
        # Fallback without sidechain (older ffmpeg builds)
        af2 = (
            f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{dur:.3f},"
            f"afade=t=in:st=0:d={intro_fade:.2f},"
            f"afade=t=out:st={max(0.0, dur - outro_fade):.3f}:d={outro_fade:.2f},"
            f"volume={ducked:.3f}[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        cmd2 = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(track),
            "-filter_complex", af2,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(out),
        ]
        _run(cmd2)
        return out


def music_library_status() -> dict[str, Any]:
    tracks = list_music_tracks("auto")
    return {
        "track_count": len(tracks),
        "music_dir": str(MUSIC_DIR),
        "extra_dir": settings.music_library_dir,
        "sample": [t.name for t in tracks[:8]],
    }
