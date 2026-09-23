"""ContentGremlin - Idea Generator with multi-signal originality filtering."""
from __future__ import annotations
from typing import Any
import json, re
from providers.llm import LLMProvider
from core.config import load_user_profile
from core.safety import enforce_originality, SafetyError

SYSTEM_PROMPT = """Eres un estratega de contenido de YouTube de alto nivel.
Generas ideas 100% ORIGINALES inspiradas en patrones de alto nivel, nunca en títulos literales.
Prohibido reutilizar títulos o frases casi idénticas. Responde SOLO con JSON válido."""

async def generate_ideas(analysis_report: dict[str, Any], count: int = 8, niche: str | None = None) -> list[dict[str, Any]]:
    profile = load_user_profile()
    user_niche = niche or profile.get("niche") or "general"
    language = profile.get("style_preferences", {}).get("language", "es")
    tone = profile.get("style_preferences", {}).get("tone", "professional yet engaging")
    patterns = analysis_report.get("patterns") or {}
    top_titles = (analysis_report.get("top_titles") or analysis_report.get("reference_titles_for_safety") or [v.get("title", "") for v in analysis_report.get("top_videos", [])[:12]] or [v.get("title", "") for v in analysis_report.get("videos_sample", [])[:12]])
    top_titles = [t for t in top_titles if t]
    common_words = patterns.get("common_topic_words") or analysis_report.get("common_title_words") or []
    avg_minutes = patterns.get("suggested_script_minutes") or analysis_report.get("average_duration_minutes") or 8
    prompt = f"""Genera {count} ideas COMPLETAMENTE ORIGINALES.
Nicho: {user_niche} | Idioma: {language} | Tono: {tone} | Duración ~{avg_minutes} min
Señales del canal (NO copiar): postura={patterns.get('content_posture')}, fórmula={patterns.get('dominant_title_formula')}, hooks={patterns.get('hook_styles_signal')}, temas={', '.join(common_words[:15])}
Títulos de referencia (prohibido imitar):
{chr(10).join(f'- {t}' for t in top_titles[:10])}
JSON: {{"ideas": [{{"title": "...", "angle": "...", "hook": "...", "why_it_works": "...", "estimated_minutes": 8}}]}}"""
    llm = LLMProvider()
    raw = await llm.generate(prompt, system=SYSTEM_PROMPT, temperature=0.85)
    ideas = []
    try:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match: ideas = (json.loads(match.group(0)).get("ideas") or [])
    except Exception:
        ideas = []
    cleaned = []
    for idea in ideas:
        blob = f"{idea.get('title','')}. {idea.get('angle','')}. {idea.get('hook','')}"
        try:
            idea["originality"] = enforce_originality(blob, top_titles, strict=True)
            cleaned.append(idea)
        except SafetyError:
            continue
    return cleaned[:count]
