# Skill: Bridge ContentGremlin → Editor

## Desde el editor

```http
POST /api/integrate/gremlin
{
  "name": "Desde Gremlin",
  "videoPath": "/abs/path/video.mp4",
  "mediaPaths": ["/abs/path/clip1.mp4"],
  "autoAssemble": true,
  "crossfade": 0.5
}
```

## Desde ContentGremlin

```http
POST http://127.0.0.1:8000/api/open_in_editor
{
  "video_path": "/abs/path/out.mp4",
  "name": "ep01",
  "auto_assemble": true
}
```

O `super_pipeline` con `"open_in_editor": true` → `editor_url`.

## Checklist

- [ ] Editor en :3000
- [ ] Paths absolutos visibles por Node
- [ ] Usuario puede abrir editor_url para refinar
