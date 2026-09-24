# Video Editor Local — Phase 3

Editor local tipo Premiere + API para agentes + FFmpeg.

## Features
- Timeline multipista, cut, ripple, reorder, crossfade (xfade)
- Preview frame at t, OTIO JSON export
- Persistent render jobs
- 10 real plugins (fade, scale, volume, blur, brightness, contrast, crop, title, crossfade)
- ContentGremlin integration (`/api/integrate/gremlin`)

## Run
```bash
cd video_editor
npm install
node server.js
```
http://localhost:3000

Requires: Node ≥ 18, ffmpeg, ffprobe.

See `docs/AGENT_SKILL.md` and `docs/PHASE3.md`.
