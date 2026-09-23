# API Video Editor

Base: `http://localhost:3000/api`

## Proyectos
POST /api/projects → {id}
GET /api/projects/:id

## Media
POST /api/media/import multipart/form-data file

## Timeline
POST /api/timeline/clips {projectId, trackId, clip}
POST /api/timeline/cut {projectId, clipId, at}
POST /api/timeline/effects {projectId, clipId, effectId, params}
POST /api/timeline/transitions {projectId, fromClipId, toClipId, transitionId, duration}

## Render
POST /api/render {projectId, width, height, outputPath}
GET /api/render/:jobId

## Agent commands de alto nivel
Importa clips, coloca segundo después del primero, añade fundido 1s y exporta 1080p
→ se traduce a secuencia de llamadas API verificables.
