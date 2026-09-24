# Skill: Analizar canal de referencia

## Objetivo

Extraer **patrones de alto nivel**. **Prohibido** copiar títulos, guiones o estructura literal.

## Llamada

```http
POST /api/analyze_channel
Content-Type: application/json

{ "channel_url": "https://www.youtube.com/@handle" }
```

Acepta handle `@name` o URL de canal.

## Respuesta

Guardá el report completo (objeto con `patterns`). Reutilizalo como `analysis_report` en ideas.

## Después

1. **Supervised:** resumí en 3–6 bullets (temas, duración, gancho). **No** pegues títulos del canal. Pedí OK.
2. **Autonomous:** pasá el report a `generate_ideas`.

## Errores

| detail | Acción |
|--------|--------|
| URL inválida | Pedir URL correcta |
| timeout | Reintentar 1 vez |
| LLM error | Verificar provider/API key |

## Anti-patrones

- No generes ideas en este paso.
- No digas “vamos a hacer el mismo video que X”.
