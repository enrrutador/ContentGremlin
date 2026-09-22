"""
ContentGremlin - Script Writer
Writes original full scripts from an approved idea.
"""

from typing import Any
from providers.llm import LLMProvider
from core.config import load_user_profile
from core.safety import enforce_originality


SYSTEM_PROMPT = """Eres un guionista profesional de YouTube.
Escribes guiones claros, con buen ritmo, hooks fuertes y valor real.
Nunca copies contenido de otros. Todo debe ser original.
Estructura recomendada:
1. Hook fuerte (primeros 10-15 segundos)
2. Promesa / qué va a aprender el espectador
3. Desarrollo con puntos claros
4. Ejemplos o historias
5. Cierre + llamada a la acción
Responde solo con el guion, sin introducciones.
"""


async def write_script(idea: dict[str, Any], language: str | None = None) -> str:
    """
    Write a complete original script based on an idea.
    """
    profile = load_user_profile()
    lang = language or profile.get("style_preferences", {}).get("language", "es")
    tone = profile.get("style_preferences", {}).get("tone", "professional yet engaging")
    minutes = idea.get("estimated_minutes", 8)

    prompt = f"""
Escribe un guion completo y original para YouTube.

Idioma: {lang}
Tono: {tone}
Duración objetivo: ~{minutes} minutos

Título de la idea: {idea.get('title', '')}
Ángulo único: {idea.get('angle', '')}
Hook sugerido: {idea.get('hook', '')}

El guion debe:
- Empezar con un hook potente
- Ser conversacional y fácil de narrar
- Tener buena retención
- Terminar con una CTA clara
- Ser 100% original

Escribe el guion listo para ser leído en voz alta.
"""

    llm = LLMProvider()
    script = await llm.generate(prompt, system=SYSTEM_PROMPT, temperature=0.7)

    enforce_originality(script)

    return script.strip()
