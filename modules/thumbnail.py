"""
ContentGremlin - Thumbnail generator
Creates simple but readable thumbnails with FFmpeg.
"""

from pathlib import Path
from typing import Optional
import subprocess
from core.config import DATA_DIR

THUMB_DIR = DATA_DIR / "thumbnails"
THUMB_DIR.mkdir(parents=True, exist_ok=True)


def create_thumbnail(
    title: str,
    output_name: Optional[str] = None,
    bg_color: str = "0x0f172a",
    accent_color: str = "0x22c55e",
    width: int = 1280,
    height: int = 720,
) -> Path:
    safe = "".join(c for c in (output_name or title) if c.isalnum() or c in "-_")[:40] or "thumb"
    out = THUMB_DIR / f"{safe}.jpg"

    text = title.replace(":", "\\:").replace("'", "").replace('"', "")[:60]
    words = text.split()
    line1, line2 = "", ""
    for w in words:
        if len(line1) < 28:
            line1 = (line1 + " " + w).strip()
        else:
            line2 = (line2 + " " + w).strip()

    vf_parts = [
        f"drawbox=x=0:y=0:w={width}:h={height}:color={bg_color}:t=fill",
        f"drawbox=x=0:y={height-120}:w={width}:h=120:color={accent_color}:t=fill",
    ]
    if line1:
        vf_parts.append(f"drawtext=text='{line1}':fontcolor=white:fontsize=52:x=(w-text_w)/2:y=(h/2)-60")
    if line2:
        vf_parts.append(f"drawtext=text='{line2}':fontcolor=white:fontsize=52:x=(w-text_w)/2:y=(h/2)+10")

    vf = ",".join(vf_parts)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={bg_color}:s={width}x{height}:d=1",
        "-vf", vf,
        "-frames:v", "1",
        str(out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"Thumbnail FFmpeg error: {result.stderr[:400]}")
    return out
