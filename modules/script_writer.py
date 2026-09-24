"""
ContentGremlin - Script Writer
Writes original full scripts from an approved idea.
"""

from __future__ import annotations

from typing import Any, Optional
from providers.llm import LLMProvider
from core.config import load_user_profile
from core.safety import enforce_originality, SafetyError


SYSTEM_PROMPT = """Eres un guionista profesional de YouTube para narración en voz alta.

Objetivo: guiones que suenen humanos, concretos y con ritmo — no relleno genérico de IA.

Reglas de calidad:
- Frases cortas y hablables. Evitá párrafos densos.
- Un solo hilo argumental claro; no listes 15 tips vacíos.
- Datos, ejemplos o mini-escenas concretas (aunque sean hipotéticas, que se sientan específicas).
- Cero clichés: "en este video veremos", "sin más preámbulos", "dale like y suscríbete" repetido cada 30s.
- CTA solo al final, una vez, natural.
- Nunca copies guiones ni estructuras frase-a-frase de otros canales.

Estructura obligatoria:
1) Hook (10–20s): tensión, pregunta o promesa concreta
2) Contexto en 2–4 frases
3) Desarrollo en 3–5 bloques con transiciones naturales
4) Un ejemplo o mini-historia
5) Cierre + un CTA

Responde SOLO con el texto del guion, listo para narrar. Sin markdown ni títulos de sección visibles.
"""


async def write_script(
    idea: dict[str, Any],
    language: str | None = None,
    reference_titles: Optional[list[str]] = None,
) -> str:
    profile = load_user_profile()
    lang = language or profile.get("style_preferences", {}).get("language", "es")
    tone = profile.get("style_preferences", {}).get("tone", "professional yet engaging")
    niche = profile.get("niche") or "general"
    minutes = idea.get("estimated_minutes", 8)
    refs = reference_titles or []

    prompt = f"""
Escribe un guion completo y ORIGINAL para YouTube.

Nicho del canal del usuario: {niche}
Idioma: {lang}
Tono: {tone}
Duración objetivo: ~{minutes} minutos (~{max(120, int(minutes) * 140)} palabras aprox.)

Idea aprobada:
- Título: {idea.get('title', '')}
- Ángulo: {idea.get('angle', '')}
- Hook sugerido: {idea.get('hook', '')}
- Por qué es original: {idea.get('why_original', idea.get('why', ''))}

Prohibido imitar estos títulos de referencia:
{chr(10).join(f'- {t}' for t in refs[:12]) or '- (ninguno)'}

Exigencias extra:
- El hook debe poder decirse en una respiración.
- Cada bloque de desarrollo aporta algo nuevo (no reformules lo mismo).
- Incluí al menos una frase memorable o contraste claro.
- Sonido natural al leer en voz alta.
"""

    llm = LLMProvider()
    script = await llm.generate(prompt, system=SYSTEM_PROMPT, temperature=0.72)
    script = (script or "").strip()

    if script.startswith("```"):
        script = script.strip("`")
        if script.lower().startswith("markdown"):
            script = script[8:]
        script = script.strip()

    try:
        enforce_originality(script, refs, strict=True)
    except SafetyError:
        retry_prompt = (
            prompt
            + "\n\nEl borrador anterior era demasiado similar a material de referencia "
            "o genérico. Reescribe con otro vocabulario, otro orden de ideas y ejemplos distintos."
        )
        script = (await llm.generate(retry_prompt, system=SYSTEM_PROMPT, temperature=0.9)).strip()
        enforce_originality(script, refs, strict=True)

    return script
