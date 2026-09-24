# Skill: Generar ideas originales

## Prerrequisito

`analysis_report` de `analyze_channel`.

## Llamada

```http
POST /api/generate_ideas
Content-Type: application/json

{
  "analysis_report": { },
  "count": 8,
  "niche": "opcional"
}
```

## Respuesta

```json
{
  "success": true,
  "ideas": [ { "title": "...", "angle": "...", "hook": "...", "why_original": "..." } ],
  "library_id": "..."
}
```

## Supervised

1. Listá ideas numeradas.
2. Esperá elección.
3. **No** escribas el script hasta que elija.

## Autonomous

Elegí idea #1 salvo otra prioridad del usuario; documentá cuál.

## Después

```http
POST /api/write_script
{ "idea": { "title": "...", "angle": "...", "hook": "..." } }
```
