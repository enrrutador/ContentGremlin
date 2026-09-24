# Phase 3

## Implemented
- OpenTimelineIO JSON: `GET /api/projects/:id/otio`
- Persistent jobs: `jobs/*.json`, `GET /api/render`
- Plugins: blur, brightness, contrast, crop, title (+ previous 5)
- ContentGremlin bridge: `POST /api/integrate/gremlin`, `modules/editor_bridge.py`

## Run
```bash
cd video_editor && npm install && node server.js
```

## Gremlin → Editor
```bash
curl -X POST http://localhost:3000/api/integrate/gremlin \
  -H "Content-Type: application/json" \
  -d '{"name":"ep01","mediaPaths":["/abs/path/to/clip.mp4"],"autoAssemble":true}'
```

## Python
```python
from modules.editor_bridge import send_to_editor
await send_to_editor(media_paths=["/path/video.mp4"], auto_assemble=True)
```
