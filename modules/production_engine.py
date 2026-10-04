"""
ContentGremlin - Production Engine
Profile-driven video assembly for publish-ready output.

Reads production config from user profile and materializes:
  TTS → scene plan → visual assets (stock / AI / still) → timeline edit
  → subtitles → music ducking → QA gate.
"""
from __future__ import annotations

import json
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from core.config import get_production_config, load_user_profile
from core.storage import get_dir
from modules.scene_planner import plan_scenes
from modules.subtitles import generate_subtitles
from modules.video_creator import create_simple_video, burn_subtitles
from modules.qa_agent import run_qa
from providers.tts import TTSProvider

OUT_DIR = get_dir("videos")
WORK_DIR = get_dir("production_work")

_PACE_CUT = {
    "slow": 6.5,
    "medium": 4.5,
    "fast": 2.8,
    "dynamic": 3.5,
}


def _run(cmd: list[str], timeout: int = 900) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"FFmpeg production error: {(r.stderr or '')[:1500]}")


def _probe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    try:
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def _parse_resolution(res: str) -> tuple[int, int]:
    try:
        w, h = res.lower().split("x")
        return int(w), int(h)
    except Exception:
        return 1920, 1080


def _new_work_dir() -> Path:
    """Work dir único por corrida + poda best-effort de dirs viejos (>24h)."""
    try:
        now = time.time()
        for child in WORK_DIR.iterdir():
            try:
                if child.is_dir() and now - child.stat().st_mtime > 24 * 3600:
                    import shutil

                    shutil.rmtree(child, ignore_errors=True)
            except Exception:
                pass
    except Exception:
        pass
    work = WORK_DIR / f"job_{uuid.uuid4().hex[:12]}"
    work.mkdir(parents=True, exist_ok=True)
    return work


def _trim_clip(src: Path, duration: float, out: Path, w: int, h: int, fps: int) -> Path:
    """Scale/crop to target and trim/loop to exact duration."""
    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},fps={fps}"
    )
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", str(src),
        "-t", f"{duration:.3f}",
        "-vf", vf,
        "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        str(out),
    ]
    _run(cmd)
    return out


def _still_clip(duration: float, out: Path, w: int, h: int, fps: int, color: str = "0x0b1220") -> Path:
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={color}:s={w}x{h}:d={duration:.3f}",
        "-vf", f"fps={fps}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(out),
    ]
    _run(cmd)
    return out


def _concat_clips(clips: list[Path], out: Path, transition: str = "none", xfade: float = 0.0) -> Path:
    if not clips:
        raise ValueError("No clips to concatenate")
    if len(clips) == 1 or transition == "none" or xfade <= 0:
        list_file = out.parent / f"{out.stem}_list.txt"
        lines = []
        for c in clips:
            p = str(c.resolve()).replace("'", "'\\''")
            lines.append(f"file '{p}'")
        list_file.write_text("\n".join(lines), encoding="utf-8")
        _run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out),
        ])
        list_file.unlink(missing_ok=True)
        return out

    # xfade chain for crossfade
    inputs: list[str] = []
    for c in clips:
        inputs.extend(["-i", str(c)])
    filter_parts = []
    durations = [_probe_duration(c) or 3.0 for c in clips]
    prev = "[0:v]"
    offset = 0.0
    for i in range(1, len(clips)):
        offset += max(0.1, durations[i - 1] - xfade)
        out_label = f"[v{i}]" if i < len(clips) - 1 else "[vout]"
        filter_parts.append(
            f"{prev}[{i}:v]xfade=transition=fade:duration={xfade:.3f}:offset={offset:.3f}{out_label}"
        )
        prev = out_label
    fc = ";".join(filter_parts)
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[vout]", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)]
    try:
        _run(cmd)
    except RuntimeError:
        # fallback concat demuxer
        return _concat_clips(clips, out, transition="none", xfade=0)
    return out


def _mux_audio(video: Path, audio: Path, out: Path) -> Path:
    _run([
        "ffmpeg", "-y",
        "-i", str(video),
        "-i", str(audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(out),
    ])
    return out


def _apply_bold_subtitles(video: Path, srt: Path, out: Path) -> Path:
    """Burn large faceless-style subtitles."""
    srt_escaped = (
        str(srt).replace("\\", "/")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )
    style = (
        "FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H80000000,BorderStyle=3,Outline=2,Shadow=0,"
        "MarginV=60,Alignment=2,Bold=1"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video),
        "-vf", f"subtitles='{srt_escaped}':force_style='{style}'",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(out),
    ]
    _run(cmd)
    return out


async def _resolve_visuals(
    scenes: list[dict[str, Any]],
    prod: dict[str, Any],
) -> list[dict[str, Any]]:
    style = prod.get("visual_style", "faceless_stock")
    broll_cfg = prod.get("broll") or {}

    if style in ("faceless_stock", "hybrid") and broll_cfg.get("enabled", True):
        from modules.broll import fetch_broll_for_scenes

        assets = await fetch_broll_for_scenes(scenes, broll_cfg)
        if style == "hybrid":
            # fill missing with still markers (AI path can be added later)
            return assets
        return assets

    if style == "faceless_ai":
        # Delegate scene images to existing cinematic image path when configured
        try:
            from providers.image import ImageProvider

            img = ImageProvider()
            if img.is_configured():
                filled = []
                for s in scenes:
                    try:
                        path = await img.generate(
                            s.get("visual_prompt") or "cinematic scene",
                            filename=f"prod_scene_{s.get('index', 0):02d}",
                        )
                        filled.append({
                            "scene_index": s.get("index"),
                            "type": "image",
                            "clip_path": str(path),
                            "duration_seconds": float(s.get("duration_seconds") or 5),
                        })
                    except Exception:
                        filled.append({
                            "scene_index": s.get("index"),
                            "type": "missing",
                            "clip_path": None,
                            "duration_seconds": float(s.get("duration_seconds") or 5),
                        })
                return filled
        except Exception:
            pass

    return [
        {
            "scene_index": s.get("index"),
            "type": "still",
            "clip_path": None,
            "duration_seconds": float(s.get("duration_seconds") or 5),
        }
        for s in scenes
    ]


async def _assemble_timeline(
    *,
    audio_path: Path,
    title: str,
    scenes: list[dict],
    assets: list[dict],
    prod: dict,
) -> Path:
    w, h = _parse_resolution(prod.get("target_resolution", "1920x1080"))
    fps = int(prod.get("fps") or 30)
    pace = prod.get("editing_pace", "medium")
    # optionally re-balance scene durations toward pace target
    target_cut = _PACE_CUT.get(pace, 4.5)
    audio_dur = _probe_duration(audio_path) or sum(float(s.get("duration_seconds") or 5) for s in scenes)

    work = _new_work_dir()

    clips: list[Path] = []
    asset_by_idx = {a.get("scene_index"): a for a in assets}

    for i, scene in enumerate(scenes):
        idx = scene.get("index", i + 1)
        dur = float(scene.get("duration_seconds") or target_cut)
        # soft pull toward pace
        dur = (dur * 0.6) + (target_cut * 0.4)
        dur = max(2.0, min(12.0, dur))
        asset = asset_by_idx.get(idx) or {}
        clip_out = work / f"clip_{idx:02d}.mp4"
        src = asset.get("clip_path")
        atype = asset.get("type")

        if src and Path(src).exists() and atype in ("stock", "image", "video"):
            try:
                _trim_clip(Path(src), dur, clip_out, w, h, fps)
            except Exception:
                _still_clip(dur, clip_out, w, h, fps)
        else:
            _still_clip(dur, clip_out, w, h, fps)
        clips.append(clip_out)

    # rescale total video duration to match audio
    total_clips = sum(_probe_duration(c) or 3.0 for c in clips)
    if total_clips > 1 and audio_dur > 1 and abs(total_clips - audio_dur) > 1.5:
        scale = audio_dur / total_clips
        scaled: list[Path] = []
        for i, c in enumerate(clips):
            d = max(2.0, (_probe_duration(c) or 3.0) * scale)
            sc_out = work / f"scaled_{i:02d}.mp4"
            _run([
                "ffmpeg", "-y", "-i", str(c),
                "-t", f"{d:.3f}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(sc_out),
            ])
            scaled.append(sc_out)
        clips = scaled

    silent = work / "timeline_silent.mp4"
    xfade = float(prod.get("transition_duration") or 0)
    transition = prod.get("transition") or "none"
    if transition == "crossfade" and xfade > 0 and len(clips) > 1:
        _concat_clips(clips, silent, transition="crossfade", xfade=xfade)
    else:
        _concat_clips(clips, silent, transition="none")

    safe = "".join(c for c in title if c.isalnum() or c in "-_")[:50] or "production"
    with_audio = OUT_DIR / f"{safe}_prod.mp4"
    _mux_audio(silent, audio_path, with_audio)
    return with_audio


def _apply_qa_gate(
    result: dict[str, Any],
    qa: dict[str, Any],
    prod: dict[str, Any],
    *,
    strict_qa: bool = False,
) -> dict[str, Any]:
    """El sistema informa, el usuario decide.

    Por defecto el video siempre se entrega (success=True) con
    publishable True/False + reasons como advisory. Solo con
    strict_qa=True el gate voltea success a False.
    """
    result["qa"] = qa
    result["publishable"] = bool(qa.get("publishable") or qa.get("ok"))
    if prod.get("quality_bar") == "publishable" and not qa.get("ok"):
        result["message"] = (
            "Video listo, pero QA no alcanzó la barra publishable "
            f"(decisión tuya publicarlo o no). Reasons: {', '.join(qa.get('reasons') or [])}"
        )
        if strict_qa:
            result["success"] = False
    return result


async def produce(
    script: str,
    title: str,
    *,
    voice: Optional[str] = None,
    idea: Optional[dict] = None,
    skip_qa: bool = False,
    strict_qa: bool = False,
) -> dict[str, Any]:
    """
    Full production pipeline driven by user production profile.
    """
    if not script or len(script.strip()) < 40:
        raise ValueError("Script too short for production")

    prod = get_production_config()
    profile = load_user_profile()
    tts = TTSProvider()
    audio_path = await tts.generate(text=script, filename=title, voice=voice)
    audio_path = Path(audio_path)
    audio_dur = _probe_duration(audio_path)

    scenes = await plan_scenes(
        script=script,
        title=title,
        total_duration_seconds=audio_dur or None,
    )
    if not scenes:
        raise RuntimeError("Scene planner returned no scenes")

    assets = await _resolve_visuals(scenes, prod)

    # If no usable stock/AI assets, fall back to simple template video (still reliable)
    usable = sum(1 for a in assets if a.get("clip_path"))
    if usable == 0 and prod.get("visual_style") in ("still",):
        video_path = create_simple_video(
            audio_path=audio_path,
            title=title,
            output_name=title,
            template="dark_minimal",
            resolution=prod.get("target_resolution", "1280x720"),
        )
    else:
        try:
            video_path = await _assemble_timeline(
                audio_path=audio_path,
                title=title,
                scenes=scenes,
                assets=assets,
                prod=prod,
            )
        except Exception as e:
            # hard fallback
            video_path = create_simple_video(
                audio_path=audio_path,
                title=title,
                output_name=title + "_fallback",
                template="dark_minimal",
            )
            assets.append({"fallback_reason": str(e)[:300]})

    video_path = Path(video_path)
    subs = generate_subtitles(script, title, audio_path=audio_path)
    sub_style = prod.get("subtitle_style", "bold_faceless")

    if sub_style == "minimal":
        burned = burn_subtitles(video_path, Path(subs["srt_path"]), output_name=title + "_subs")
        video_path = Path(burned)
    elif sub_style in ("bold_faceless", "karaoke"):
        out_subs = OUT_DIR / f"{video_path.stem}_subs.mp4"
        try:
            video_path = _apply_bold_subtitles(video_path, Path(subs["srt_path"]), out_subs)
        except Exception:
            burned = burn_subtitles(video_path, Path(subs["srt_path"]), output_name=title + "_subs")
            video_path = Path(burned)

    music_meta: dict[str, Any] = {"applied": False}
    music_cfg = prod.get("music") or {}
    if music_cfg.get("enabled"):
        try:
            from modules.audio_mix import mix_music_under_video

            mixed = mix_music_under_video(
                video_path,
                intensity=float(music_cfg.get("intensity", 0.22)),
                duck_strength=float(music_cfg.get("duck_strength", 0.65)),
                mood=str(music_cfg.get("mood", "auto")),
                intro_fade=float(music_cfg.get("intro_fade_seconds", 1.5)),
                outro_fade=float(music_cfg.get("outro_fade_seconds", 2.0)),
                output_name=title + "_final",
            )
            if Path(mixed) != video_path:
                video_path = Path(mixed)
                music_meta = {"applied": True, "path": str(mixed)}
        except Exception as e:
            music_meta = {"applied": False, "error": str(e)[:300]}

    result: dict[str, Any] = {
        "success": True,
        "video_path": str(video_path),
        "audio_path": str(audio_path),
        "srt_path": subs.get("srt_path"),
        "vtt_path": subs.get("vtt_path"),
        "scenes": scenes,
        "assets": assets,
        "visual_style": prod.get("visual_style"),
        "editing_pace": prod.get("editing_pace"),
        "subtitle_style": sub_style,
        "music": music_meta,
        "quality_bar": prod.get("quality_bar"),
        "niche": profile.get("niche"),
        "size_bytes": video_path.stat().st_size if video_path.exists() else 0,
    }

    if not skip_qa:
        qa = run_qa(video_path, audio_path=audio_path, script=script, prod=prod)
        _apply_qa_gate(result, qa, prod, strict_qa=strict_qa)
    else:
        result["publishable"] = None

    return result
