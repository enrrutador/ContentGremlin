"""Cinematic pipeline: scenes → image/video → Ken Burns/concat → audio → optional subs."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Optional
import subprocess, json
from core.config import DATA_DIR, settings
from modules.scene_planner import plan_scenes
from modules.subtitles import generate_subtitles
from modules.video_creator import burn_subtitles
from providers.image import ImageProvider
from providers.video_gen import VideoGenProvider
from providers.tts import TTSProvider

OUT_DIR = DATA_DIR / "cinematic" / "out"
SCENE_DIR = DATA_DIR / "cinematic" / "scenes"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SCENE_DIR.mkdir(parents=True, exist_ok=True)

def _run(cmd: list[str], timeout: int = 600) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {r.stderr[:1200]}")

def _probe_duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)], capture_output=True, text=True)
    try:
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        return 5.0

def _motion_filter(motion: str, duration: float, w: int = 1280, h: int = 720) -> str:
    frames = max(1, int(duration * 30))
    if motion == "slow_zoom_out":
        return f"scale=8000:-1,zoompan=z='if(eq(on,1),1.3,max(1.0,zoom-0.0008))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps=30"
    if motion == "pan_left":
        return f"scale=2000:-1,zoompan=z='1.15':x='if(eq(on,1),iw*0.2,max(0,x-2))':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps=30"
    if motion == "pan_right":
        return f"scale=2000:-1,zoompan=z='1.15':x='if(eq(on,1),0,min(iw-iw/zoom,x+2))':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps=30"
    if motion == "static":
        return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps=30"
    return f"scale=8000:-1,zoompan=z='min(1.25,zoom+0.0008)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps=30"

def _image_to_clip(image: Path, duration: float, motion: str, out: Path) -> Path:
    vf = _motion_filter(motion, duration)
    _run(["ffmpeg", "-y", "-loop", "1", "-i", str(image), "-vf", vf, "-t", f"{duration:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(out)])
    return out

def _concat_clips(clips: list[Path], out: Path) -> Path:
    list_file = out.parent / f"{out.stem}_list.txt"
    lines = [f"file '{str(c.resolve()).replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'" for c in clips]
    list_file.write_text("\n".join(lines), encoding="utf-8")
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])
    return out

def _mux_audio(video: Path, audio: Path, out: Path) -> Path:
    _run(["ffmpeg", "-y", "-i", str(video), "-i", str(audio), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)])
    return out

async def create_cinematic_video(script: str, title: str, voice: Optional[str] = None, burn_subs: bool = False, style: Optional[str] = None) -> dict[str, Any]:
    image_p = ImageProvider()
    if not image_p.is_configured():
        raise RuntimeError("Cinematic mode needs image provider. Set OPENAI_API_KEY and IMAGE_PROVIDER=openai.")
    tts = TTSProvider()
    audio_path = await tts.generate(text=script, filename=title, voice=voice)
    audio_dur = _probe_duration(Path(audio_path))
    scenes = await plan_scenes(script=script, title=title, total_duration_seconds=audio_dur, style=style)
    video_p = VideoGenProvider()
    clips, scene_assets = [], []
    for scene in scenes:
        idx, prompt, dur = scene["index"], scene["visual_prompt"], float(scene["duration_seconds"])
        motion = scene.get("motion") or "slow_zoom_in"
        asset = {"index": idx, "prompt": prompt, "duration": dur, "motion": motion}
        clip_path = SCENE_DIR / f"scene_{idx:02d}.mp4"
        gen_clip = None
        if video_p.is_configured():
            try:
                gen_clip = await video_p.generate_clip(prompt, dur, f"clip_{idx:02d}")
            except Exception as e:
                asset["video_error"] = str(e)
        if gen_clip and Path(gen_clip).exists():
            _run(["ffmpeg", "-y", "-i", str(gen_clip), "-t", f"{dur:.3f}", "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,fps=30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(clip_path)])
            asset["source"] = "video_api"
        else:
            img = await image_p.generate(prompt, filename=f"scene_{idx:02d}")
            asset["image_path"] = str(img)
            _image_to_clip(img, dur, motion, clip_path)
            asset["source"] = "image_kenburns"
        asset["clip_path"] = str(clip_path)
        clips.append(clip_path)
        scene_assets.append(asset)
    safe = "".join(c for c in title if c.isalnum() or c in "-_")[:40] or "cinematic"
    silent, with_audio = OUT_DIR / f"{safe}_silent.mp4", OUT_DIR / f"{safe}.mp4"
    _concat_clips(clips, silent)
    _mux_audio(silent, Path(audio_path), with_audio)
    result = {"mode": "cinematic", "video_path": str(with_audio), "audio_path": str(audio_path), "title": title, "scenes": scene_assets, "size_bytes": with_audio.stat().st_size if with_audio.exists() else 0, "image_provider": image_p.provider, "video_provider": video_p.provider, "video_provider_used": video_p.is_configured()}
    subs = generate_subtitles(script, title, audio_path=audio_path)
    result["srt_path"], result["vtt_path"] = subs["srt_path"], subs["vtt_path"]
    if burn_subs:
        burned = burn_subtitles(with_audio, Path(subs["srt_path"]), output_name=safe + "_subs")
        result["video_path"] = str(burned)
        result["subtitles_burned"] = True
        result["size_bytes"] = burned.stat().st_size if burned.exists() else 0
    return result
