# API Video Editor

Base: `http://localhost:3000/api`

## Projects
- POST /api/projects
- GET /api/projects | GET /api/projects/:id | DELETE /api/projects/:id

## Media
- POST /api/media/import (file + projectId) → duration via ffprobe
- GET /api/projects/:id/media

## Timeline
- POST /api/timeline/clips
- POST /api/timeline/cut | trim
- POST /api/timeline/move `{ clipId, start? }` o `{ order: [clipIds] }`
- POST /api/timeline/ripple `{ trackId }`
- DELETE /api/timeline/clips/:id?projectId=&ripple=true
- POST /api/timeline/effects | transitions

## Preview
- GET /api/preview/info?projectId=
- GET /api/preview/frame?projectId=&t=

## Render / Agent
- POST /api/render → jobId
- GET /api/render/:jobId
- POST /api/agent/assemble `{ projectId, mediaIds, crossfade, fadeInFirst, width, height }`
- GET /api/plugins
