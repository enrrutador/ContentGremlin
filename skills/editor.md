# Skill: Editor local (puente desde Gremlin)

**Docs de montaje:** `video_editor/skills/SKILL.md`

## Abrir media en el editor

```http
POST /api/open_in_editor
Content-Type: application/json

{
  "video_path": "/abs/path/out.mp4",
  "media_paths": ["/abs/path/clip2.mp4"],
  "name": "ep01",
  "auto_assemble": true,
  "crossfade": 0.5
}
```

```json
{
  "success": true,
  "editor_project_id": "...",
  "editor_url": "http://127.0.0.1:3000/?projectId=..."
}
```

Alternativa: `super_pipeline` con `"open_in_editor": true`.

Requisito: editor en `:3000`. El MP4 final del render del editor es el path para `upload_video`.
