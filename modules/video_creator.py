"""ContentGremlin - Video Creator with templates (still + voice). Requires FFmpeg."""
from __future__ import annotations
from pathlib import Path
from typing import Optional
import subprocess, json, re
from core.config import DATA_DIR

VIDEO_DIR = DATA_DIR / "videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATES = {
    "dark_minimal": {"bg": "0x0b1220", "accent": "0x22c55e", "title_color": "white", "subtitle_color": "0x94a3b8"},
    "studio_blue": {"bg": "0x0f172a", "accent": "0x38bdf8", "title_color": "white", "subtitle_color": "0xcbd5e1"},
    "warm_editorial": {"bg": "0x1c1917", "accent": "0xf59e0b", "title_color": "0xfafaf9", "subtitle_color": "0xd6d3d1"},
}

def _run_ffmpeg(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr[:1000]}")

def _probe_duration(path: Path) -> float:
    probe = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)], capture_output=True, text=True)
    try:
        return float(json.loads(probe.stdout)["format"]["duration"])
    except Exception:
        return 10.0

def _escape_drawtext(text: str, max_len: int = 70) -> str:
    t = text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "").replace('"', "")
    return re.sub(r"[\n\r\t]+", " ", t).strip()[:max_len]

def _split_title_lines(title: str, max_chars: int = 28) -> list[str]:
    words, lines, buf = title.split(), [], []
    for w in words:
        trial = (" ".join(buf + [w])).strip()
        if len(trial) <= max_chars: buf.append(w)
        else:
            if buf: lines.append(" ".join(buf))
            buf = [w]
        if len(lines) >= 2: break
    if buf and len(lines) < 3: lines.append(" ".join(buf))
    return lines[:3] or [title[:max_chars]]

def create_simple_video(audio_path: Path, title: str = "ContentGremlin Video", output_name: Optional[str] = None, template: str = "dark_minimal", resolution: str = "1280x720", show_progress: bool = True) -> Path:
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio not found: {audio_path}")
    style = TEMPLATES.get(template, TEMPLATES["dark_minimal"])
    safe_name = "".join(c for c in (output_name or "video") if c.isalnum() or c in "-_")[:50]
    out_path = VIDEO_DIR / f"{safe_name}.mp4"
    duration = _probe_duration(audio_path)
    lines = _split_title_lines(title)
    esc_lines = [_escape_drawtext(L) for L in lines]
    w, h = 1280, 720
    if "x" in resolution:
        try: w, h = [int(x) for x in resolution.split("x")]
        except Exception: pass
    vf_parts = [
        f"drawbox=x=0:y=0:w={w}:h={h}:color={style['bg']}:t=fill",
        f"drawbox=x=0:y=0:w={w}:h=8:color={style['accent']}:t=fill",
        f"drawbox=x=48:y={h-56}:w={w-96}:h=4:color=0x334155:t=fill",
    ]
    base_y = h // 2 - 40 * len(esc_lines)
    for i, line in enumerate(esc_lines):
        y = base_y + i * 52
        vf_parts.append(f"drawtext=text='{line}':fontcolor={style['title_color']}:fontsize=44:x=(w-text_w)/2:y={y}")
    vf_parts.append(f"drawtext=text='ContentGremlin':fontcolor={style['subtitle_color']}:fontsize=18:x=48:y={h-40}")
    vf = ",".join(vf_parts)
    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={style['bg']}:s={w}x{h}:d={duration}", "-i", str(audio_path), "-vf", vf, "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out_path)]
    _run_ffmpeg(cmd)
    return out_path

def burn_subtitles(video_path: Path, srt_path: Path, output_name: Optional[str] = None) -> Path:
    safe = "".join(c for c in (output_name or video_path.stem + "_subs") if c.isalnum() or c in "-_")[:50]
    out = VIDEO_DIR / f"{safe}.mp4"
    srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    cmd = ["ffmpeg", "-y", "-i", str(video_path), "-vf", f"subtitles='{srt_escaped}':force_style='FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=40'", "-c:a", "copy", "-movflags", "+faststart", str(out)]
    _run_ffmpeg(cmd)
    return out

def create_video_from_script_and_audio(script: str, audio_path: Path, title: str, output_name: Optional[str] = None, srt_path: Optional[Path] = None, burn_subs: bool = False, template: str = "dark_minimal") -> dict:
    video_path = create_simple_video(audio_path=audio_path, title=title, output_name=output_name, template=template)
    result = {"video_path": str(video_path), "audio_path": str(audio_path), "title": title, "template": template, "size_bytes": video_path.stat().st_size if video_path.exists() else 0}
    if burn_subs and srt_path and Path(srt_path).exists():
        burned = burn_subtitles(video_path, Path(srt_path), output_name=(output_name or title) + "_subs")
        result["video_path"] = str(burned)
        result["subtitles_burned"] = True
        result["size_bytes"] = burned.stat().st_size if burned.exists() else 0
    return result
