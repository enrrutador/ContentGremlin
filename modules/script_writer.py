"""ContentGremlin - Script Writer with originality retry."""
from __future__ import annotations
from typing import Any, Optional
from providers.llm import LLMProvider
from core.config import load_user_profile
from core.safety import enforce_originality, SafetyError

SYSTEM_PROMPT = """Eres un guionista profesional de YouTube.
Escribes guiones claros, con ritmo, hooks fuertes y valor real.
Nunca copies guiones ni estructuras frase-a-frase de otros canales.
Estructura: Hook (10-15s) -> Promesa -> Desarrollo -> Ejemplo -> Cierre + CTA.
Responde solo con el guion listo para narrar."""

async def write_script(idea: dict[str, Any], language: str | None = None, reference_titles: Optional[list[str]] = None) -> str:
    profile = load_user_profile()
    lang = language or profile.get("style_preferences", {}).get("language", "es")
    tone = profile.get("style_preferences", {}).get("tone", "professional yet engaging")
    minutes = idea.get("estimated_minutes", 8)
    refs = reference_titles or []
    prompt = f"""Escribe un guion completo y original para YouTube.
Idioma: {lang}
Tono: {tone}
Duración objetivo: ~{minutes} minutos
Título: {idea.get('title', '')}
Ángulo: {idea.get('angle', '')}
Hook sugerido: {idea.get('hook', '')}
Prohibido imitar estos títulos de referencia:
{chr(10).join(f'- {t}' for t in refs[:12])}
Conversacional, fácil de narrar, buena retención, CTA final."""
    llm = LLMProvider()
    script = (await llm.generate(prompt, system=SYSTEM_PROMPT, temperature=0.7) or "").strip()
    if script.startswith("```"):
        script = script.strip("`")
        if script.lower().startswith("markdown"): script = script[8:]
        script = script.strip()
    try:
        enforce_originality(script, refs, strict=True)
    except SafetyError:
        retry = prompt + "\n\nTu borrador anterior era demasiado similar. Reescribe con otro ángulo y vocabulario distinto."
        script = (await llm.generate(retry, system=SYSTEM_PROMPT, temperature=0.9)).strip()
        enforce_originality(script, refs, strict=True)
    return script
