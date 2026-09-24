# Video Editor Local MVP (Phase 1)

Editor local inspirado en Premiere con API para agentes. Procesamiento con FFmpeg.

## Arranque

```bash
cd video_editor
npm install
node server.js
```

Abrir **http://localhost:3000**

Requisitos: Node ≥ 18, `ffmpeg` y `ffprobe` en el PATH.

## Qué funciona (Fase 1)

| Función | Estado |
|---------|--------|
| Crear / listar / cargar proyectos (JSON local) | ✅ |
| Importar medios al proyecto + duración real (`ffprobe`) | ✅ |
| Timeline multipista (`v1`, `a1`) con start, inPoint, outPoint, duration, sourcePath | ✅ |
| Añadir clips desde media del proyecto | ✅ |
| Cut que parte un clip en dos | ✅ |
| Trim / borrar clip | ✅ |
| Efectos: fade in/out, scale, volume | ✅ |
| Transiciones registradas (crossfade) | ✅ |
| Render que concatena la timeline | ✅ |
| Jobs de render async + URL | ✅ |
| UI mínima usable | ✅ |

## API (agente)

```
POST /api/projects
GET  /api/projects
GET  /api/projects/:id
POST /api/media/import          (multipart: file + projectId)
GET  /api/projects/:id/media
POST /api/timeline/clips
POST /api/timeline/cut
POST /api/timeline/trim
POST /api/timeline/effects
POST /api/timeline/transitions
POST /api/render
GET  /api/render/:jobId
GET  /api/plugins
```

## Plugins reales (`plugins/examples/`)

- effect.fade_in / effect.fade_out
- effect.scale
- effect.volume
- transition.crossfade

El catálogo ya no finge 200 módulos implementados.

## Roadmap

Ver `docs/ROADMAP.md`.
