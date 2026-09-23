"""
ContentGremlin - Metadata
Titles, descriptions, tags, and auto chapters.
"""

from typing import Any, Optional
from providers.llm import LLMProvider
from core.config import load_user_profile


async def generate_metadata(
    script: str,
    idea: Optional[dict] = None,
    language: Optional[str] = None,
) -> dict[str, Any]:
    profile = load_user_profile()
    lang = language or profile.get("style_preferences", {}).get("language", "es")
    title_hint = (idea or {}).get("title", "")

    system = """Eres un experto en SEO y metadata de YouTube.
Generas títulos atractivos, descripciones optimizadas, tags y capítulos.
Responde SOLO con JSON válido."""

    prompt = f"""
A partir de este guion de YouTube, genera metadata optimizada.

Idioma: {lang}
Título sugerido de la idea: {title_hint}

Guion (extracto):
{script[:3000]}

Devuelve JSON con esta estructura exacta:
{{
  "title": "título final optimizado para CTR (máx 70 caracteres)",
  "description": "descripción completa con gancho, valor y CTA.",
  "tags": ["tag1", "tag2"],
  "chapters": [
    {{"time": "0:00", "label": "Introducción"}},
    {{"time": "0:45", "label": "Punto 1"}}
  ]
}}
"""

    llm = LLMProvider()
    raw = await llm.generate(prompt, system=system, temperature=0.6)

    import json
    import re

    try:
        match = re.search(r"\{[\s\S]*\}", raw)
        data = json.loads(match.group(0)) if match else {}
    except Exception:
        data = {}

    title = data.get("title") or title_hint or "Video sin título"
    description = data.get("description") or script[:500]
    tags = data.get("tags") or []
    chapters = data.get("chapters") or [{"time": "0:00", "label": "Inicio"}]

    chapter_block = "\n".join(f"{c.get('time', '0:00')} {c.get('label', '')}" for c in chapters)
    full_description = f"{description.strip()}\n\n📌 Capítulos:\n{chapter_block}\n"

    return {
        "title": title[:100],
        "description": full_description,
        "tags": tags[:30],
        "chapters": chapters,
        "chapter_block": chapter_block,
    }
