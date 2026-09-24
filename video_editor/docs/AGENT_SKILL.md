# Skill: Video Editor local (agente)

Base URL: `http://localhost:3000`

## Flujo rápido
1. POST /api/projects
2. POST /api/media/import (file + projectId)
3. POST /api/agent/assemble { projectId, mediaIds, crossfade, fadeInFirst }
4. Poll GET /api/render/{jobId}

## OTIO export
`GET /api/projects/:id/otio` → OpenTimelineIO-compatible JSON

## Jobs persistentes
`GET /api/render` lista jobs (`jobs/*.json`)
`GET /api/render/:jobId` sobrevive reinicios

## Integración ContentGremlin
```json
POST /api/integrate/gremlin
{
  "name": "ep01",
  "videoPath": "/path/to/output.mp4",
  "mediaPaths": ["/path/clip1.mp4"],
  "autoAssemble": true,
  "crossfade": 0.5
}
```
Python: `modules/editor_bridge.py` → `send_to_editor(...)`

## Plugins (10)
effect.fade_in/out, scale, volume, blur, brightness, contrast, crop, title, transition.crossfade
