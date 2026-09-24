# Phase 4 (implementado)

## Features
- Render progress: job.percent + job.phase
- POST /api/preview/montage (preview 640x360)
- POST /api/projects/:id/otio/import
- Plugins: sepia, hflip, vflip, speed, loudnorm (15 total)
- UI: barra progreso, path Gremlin, OTIO export/import

## Arranque
```bash
cd video_editor && npm install && node server.js
```

El servidor completo vive en `server.monolith.js` (local) o `server.payload.a.b64`+`server.payload.b.b64`.
Si solo tenés el monolito: `USE_MONOLITH=1 node server.js`
