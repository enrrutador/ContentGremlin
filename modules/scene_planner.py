"""Split a script into timed visual scenes with image/video prompts."""
from __future__ import annotations
from typing import Any, Optional
import json, re
from providers.llm import LLMProvider
from core.config import settings

SYSTEM = """Eres un director de fotografía para YouTube faceless.
Partes un guion en escenas de 3-8s. Prompt visual en INGLÉS, sin texto en imagen.
Responde SOLO JSON válido."""

async def plan_scenes(script: str, title: str = "", max_scenes: Optional[int] = None, style: Optional[str] = None, total_duration_seconds: Optional[float] = None) -> list[dict[str, Any]]:
    max_scenes = max_scenes or settings.cinematic_max_scenes
    style = style or settings.cinematic_default_style
    prompt = f"""Divide este guion en max {max_scenes} escenas.
Título: {title}
Duración audio (s): {total_duration_seconds or "desconocida"}
Estilo: {style}
Guion:
{script[:6000]}
JSON: {{"scenes": [{{"index": 1, "narration_excerpt": "...", "duration_seconds": 5.0, "visual_prompt": "English cinematic prompt", "motion": "slow_zoom_in", "mood": "neutral"}}]}}"""
    llm = LLMProvider()
    raw = await llm.generate(prompt, system=SYSTEM, temperature=0.6)
    scenes = []
    try:
        m = re.search(r"\{[\s\S]*\}", raw)
        if m: scenes = (json.loads(m.group(0)).get("scenes") or [])
    except Exception:
        scenes = []
    if not scenes:
        parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", script) if p.strip()]
        n = min(len(parts), max_scenes) or 1
        chunk = max(1, len(parts) // n)
        for i in range(n):
            excerpt = " ".join(parts[i*chunk:(i+1)*chunk])[:200]
            scenes.append({"index": i+1, "narration_excerpt": excerpt, "duration_seconds": 5.0, "visual_prompt": f"{style}, visual metaphor for: {excerpt[:120]}", "motion": "slow_zoom_in", "mood": "neutral"})
    cleaned = []
    for i, s in enumerate(scenes[:max_scenes], 1):
        dur = max(2.5, min(12.0, float(s.get("duration_seconds") or 5)))
        cleaned.append({"index": i, "narration_excerpt": str(s.get("narration_excerpt") or "")[:300], "duration_seconds": dur, "visual_prompt": str(s.get("visual_prompt") or style)[:900], "motion": s.get("motion") or "slow_zoom_in", "mood": s.get("mood") or "neutral"})
    if total_duration_seconds and total_duration_seconds > 1 and cleaned:
        total = sum(s["duration_seconds"] for s in cleaned)
        if total > 0:
            scale = total_duration_seconds / total
            for s in cleaned:
                s["duration_seconds"] = round(max(2.5, s["duration_seconds"] * scale), 2)
    return cleaned
