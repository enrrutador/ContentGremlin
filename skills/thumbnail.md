# Skill: Miniatura

```http
POST /api/generate_thumbnail
Content-Type: application/json

{
  "title": "Título del video",
  "output_name": "ep01"
}
```

## Respuesta

```json
{ "success": true, "thumbnail_path": "/abs/path/thumb.png", "library_id": "..." }
```

Pasá `thumbnail_path` a `upload_video` si corresponde.
