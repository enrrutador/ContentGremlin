# Skill: Escribir guion

## Prerrequisito

Una `idea` aprobada.

## Llamada

```http
POST /api/write_script
Content-Type: application/json

{
  "idea": { "title": "...", "angle": "...", "hook": "..." },
  "language": "es"
}
```

## Respuesta

```json
{ "success": true, "script": "...texto completo...", "title": "...", "library_id": "..." }
```

Guardá `script` **completo** (no lo resumas al pasar al pipeline).

## Supervised

Mostrá el guion; esperá OK o cambios.

## Autonomous

Pasá a `super_pipeline` (o voice → video).

## Anti-patrones

- No acortes el script al enviarlo.
- No mezcles texto del canal de referencia.
