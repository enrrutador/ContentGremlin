# Skill: Metadata YouTube

```http
POST /api/generate_metadata
Content-Type: application/json

{
  "script": "...",
  "idea": { "title": "...", "angle": "..." },
  "language": "es"
}
```

## Respuesta

```json
{
  "success": true,
  "metadata": {
    "title": "...",
    "description": "...",
    "tags": ["..."],
    "chapters": []
  },
  "library_id": "..."
}
```

Usá esos campos en `upload_video`. En supervised, mostrá título/tags antes de subir.
