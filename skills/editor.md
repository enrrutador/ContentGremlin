# Skill: Video Editor local

Base: `http://127.0.0.1:3000`

Docs completas: `video_editor/skills/SKILL.md` y playbooks.

## Flujo mínimo

1. `POST /api/projects` → projectId
2. `POST /api/media/import-paths` `{ projectId, paths: [...] }` → mediaIds
3. `POST /api/agent/assemble` `{ projectId, mediaIds, crossfade: 1, fadeInFirst: true }` → jobId
4. Poll `GET /api/render/{jobId}` hasta `done`
5. Entregar `url` o `outputPath`

## Estado y efectos

- `GET /api/agent/status?projectId=`
- `GET /api/agent/effects`

## Desde Gremlin

`POST /api/open_in_editor` o `super_pipeline` con `open_in_editor: true`.
