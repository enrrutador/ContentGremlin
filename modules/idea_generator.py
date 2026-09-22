"""
ContentGremlin - Idea Generator
Creates original video ideas based on channel patterns + user niche.
Never copies existing titles or concepts literally.
"""

from typing import Any
from providers.llm import LLMProvider
from core.config import load_user_profile
from core.safety import enforce_originality


SYSTEM_PROMPT = """Eres un estratega de contenido de YouTube de alto nivel.
Tu trabajo es generar ideas 100% ORIGINALES inspiradas en patrones de canales exitosos.

Reglas estrictas:
- NUNCA copies títulos, estructuras o conceptos de forma literal.
- Usa solo patrones de alto nivel (temas, formato, duración, tipo de hook).
- Cada idea debe aportar un ángulo nuevo, un giro o un valor diferente.
- Prioriza curiosidad, claridad y potencial de retención.
- Responde SIEMPRE en el idioma que se te indique.
- Devuelve exactamente el formato pedido, sin texto extra.
"""


async def generate_ideas(
    analysis_report: dict[str, Any],
    count: int = 8,
    niche: str | None = None,
) -> list[dict[str, Any]]:
    """
    Generate original ideas from a channel analysis report.
    """
    profile = load_user_profile()
    user_niche = niche or profile.get("niche") or "general"
    language = profile.get("style_preferences", {}).get("language", "es")
    tone = profile.get("style_preferences", {}).get("tone", "professional yet engaging")

    patterns = analysis_report.get("patterns", {})
    top_titles = [v.get("title", "") for v in analysis_report.get("top_videos", [])[:8]]
    common_words = analysis_report.get("common_title_words", [])[:10]
    avg_minutes = analysis_report.get("average_duration_minutes", 8)

    prompt = f"""
Analiza estos patrones de un canal exitoso y genera {count} ideas de video COMPLETAMENTE ORIGINALES.

Nicho del usuario: {user_niche}
Idioma de salida: {language}
Tono deseado: {tone}
Duración promedio del canal de referencia: ~{avg_minutes} minutos

Palabras frecuentes en títulos del canal de referencia (solo como señal de temas): {', '.join(common_words)}
Algunos títulos de referencia (NO los copies, solo entiéndelos como ejemplos de lo que funciona):
{chr(10).join(f'- {t}' for t in top_titles)}

Patrones detectados: {patterns}

Genera exactamente {count} ideas. Cada idea debe tener:
- title: título original y atractivo
- angle: el ángulo único o giro que la hace diferente
- hook: la primera frase o idea de apertura (hook)
- why_it_works: por qué tiene potencial (1-2 frases)
- estimated_minutes: duración sugerida

Responde ÚNICAMENTE con un JSON válido con esta estructura:
{{
  "ideas": [
    {{
      "title": "...",
      "angle": "...",
      "hook": "...",
      "why_it_works": "...",
      "estimated_minutes": 8
    }}
  ]
}}
"""

    llm = LLMProvider()
    raw = await llm.generate(prompt, system=SYSTEM_PROMPT, temperature=0.85)

    import json
    import re

    ideas = []
    try:
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            data = json.loads(match.group(0))
            ideas = data.get("ideas", [])
        else:
            ideas = []
    except Exception:
        ideas = []

    reference_snippets = top_titles
    cleaned = []
    for idea in ideas:
        title = idea.get("title", "")
        try:
            enforce_originality(title + " " + idea.get("angle", ""), reference_snippets)
            cleaned.append(idea)
        except Exception:
            continue

    return cleaned[:count]
