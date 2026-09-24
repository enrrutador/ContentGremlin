# API Video Editor

Base: `http://localhost:3000/api`

## Projects
- `POST /api/projects` `{ name? }` → `{ id, project }`
- `GET /api/projects` → lista
- `GET /api/projects/:id`
- `DELETE /api/projects/:id`

## Media
- `POST /api/media/import` multipart `file` + field `projectId`  
  Respuesta incluye `duration`, `width`, `height`, `url` y se guarda en el proyecto.
- `GET /api/projects/:id/media`

## Timeline
- `POST /api/timeline/clips`  
  `{ projectId, trackId, mediaId, start?, inPoint?, outPoint?, duration?, effects? }`
- `POST /api/timeline/cut`  
  `{ projectId, clipId, at? }` o `{ atRelative? }`
- `POST /api/timeline/trim`  
  `{ projectId, clipId, inPoint?, outPoint?, start?, duration? }`
- `DELETE /api/timeline/clips/:clipId?projectId=`
- `POST /api/timeline/effects`  
  `{ projectId, clipId, effectId, params }`
- `POST /api/timeline/transitions`  
  `{ projectId, fromClipId, toClipId, transitionId, duration }`

## Render
- `POST /api/render` `{ projectId, width?, height?, outputPath? }` → `{ jobId }`
- `GET /api/render/:jobId` → `{ status, url?, error? }`

## Plugins
- `GET /api/plugins` → manifiestos desde `plugins/examples/`
