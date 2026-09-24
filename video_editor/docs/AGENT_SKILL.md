# Skill: Video Editor local (agente)

Base URL: `http://localhost:3000`

## Objetivo
Importar medios, armar timeline, cortar, transiciones y exportar MP4 — sin subir archivos a la nube.

## Flujo recomendado

1. `POST /api/projects` `{ "name": "ep01" }` → `projectId`
2. Por cada archivo: `POST /api/media/import` multipart field `file` + `projectId` → guardar `mediaId` y `duration`
3. **Opción rápida (alto nivel):**
   ```json
   POST /api/agent/assemble
   {
     "projectId": "...",
     "mediaIds": ["id1", "id2", "id3"],
     "crossfade": 1,
     "fadeInFirst": true,
     "width": 1920,
     "height": 1080
   }
   ```
   → `jobId`. Poll `GET /api/render/{jobId}` hasta `status=done` y usar `url`.

4. **Opción paso a paso:**
   - `POST /api/timeline/clips` `{ projectId, trackId: "v1", mediaId }`
   - `POST /api/timeline/cut` `{ projectId, clipId, atRelative: 2 }`
   - `POST /api/timeline/effects` `{ projectId, clipId, effectId: "effect.fade_in", params: { duration: 1 } }`
   - `POST /api/timeline/transitions` `{ projectId, fromClipId, toClipId, transitionId: "transition.crossfade", duration: 1 }`
   - `POST /api/timeline/move` `{ projectId, clipId, order: ["idA","idB","idC"] }`
   - `DELETE /api/timeline/clips/{clipId}?projectId=...&ripple=true`
   - `POST /api/timeline/ripple` `{ projectId, trackId: "v1" }`
   - `POST /api/render` → poll job

## Preview
- `GET /api/preview/info?projectId=` → duración total
- `GET /api/preview/frame?projectId=&t=3.5` → JPEG del fotograma en tiempo de timeline

## Plugins
`GET /api/plugins` → fade_in, fade_out, scale, volume, crossfade

## Reglas
- Usar solo `mediaId` de import.
- Mostrar `jobId`/`url` al usuario antes de publicar.
- Crossfade requiere ≥2 clips y transición (assemble lo hace solo).
