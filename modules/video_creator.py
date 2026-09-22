"""
ContentGremlin - Basic Video Creator
Creates a simple video from narration audio + optional background.
Uses FFmpeg (must be installed on the system).
"""

from pathlib import Path
from typing import Optional
import subprocess
import json
from core.config import DATA_DIR

VIDEO_DIR = DATA_DIR / "videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def _run_ffmpeg(cmd: list[str]) -> None:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr[:800]}")


def create_simple_video(
    audio_path: Path,
    title: str = "ContentGremlin Video",
    output_name: Optional[str] = None,
    background_color: str = "0x111827",
    resolution: str = "1280x720",
) -> Path:
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio not found: {audio_path}")

    safe_name = output_name or "video"
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in "-_")[:50]
    out_path = VIDEO_DIR / f"{safe_name}.mp4"

    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(audio_path)],
        capture_output=True,
        text=True,
    )
    duration = 10.0
    try:
        info = json.loads(probe.stdout)
        duration = float(info["format"]["duration"])
    except Exception:
        pass

    safe_title = title.replace(":", "\\:").replace("'", "").replace('"', "")[:80]

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={background_color}:s={resolution}:d={duration}",
        "-i", str(audio_path),
        "-vf", f"drawtext=text='{safe_title}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(out_path),
    ]

    _run_ffmpeg(cmd)
    return out_path


def create_video_from_script_and_audio(
    script: str,
    audio_path: Path,
    title: str,
    output_name: Optional[str] = None,
) -> dict:
    video_path = create_simple_video(
        audio_path=audio_path,
        title=title,
        output_name=output_name,
    )
    return {
        "video_path": str(video_path),
        "audio_path": str(audio_path),
        "title": title,
        "size_bytes": video_path.stat().st_size if video_path.exists() else 0,
    }
