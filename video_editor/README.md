# Video Editor Local — Phase 2

## New in Phase 2
- Timeline preview frame: `GET /api/preview/frame?projectId=&t=`
- Reorder clips: `POST /api/timeline/move` with `order: [ids]`
- Ripple delete: `DELETE .../clips/:id?ripple=true`
- Close gaps: `POST /api/timeline/ripple`
- Crossfade in render (ffmpeg `xfade`)
- Agent one-shot: `POST /api/agent/assemble`

## Run
```bash
cd video_editor && npm install && node server.js
```
Open http://localhost:3000

See `docs/AGENT_SKILL.md` for agent workflow.

## Phase 1 (still included)
Import + ffprobe, timeline clips, cut, trim, effects, render concat.
