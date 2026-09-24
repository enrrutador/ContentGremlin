# Video Editor Local — Phase 3

Editor local + API agentes + FFmpeg.

## Run
```bash
cd video_editor
npm install
node server.js
```
http://localhost:3000

Requires Node ≥ 18, ffmpeg, ffprobe.

`server.js` joins `server.part0.js` + `server.part1.js` + `server.part2.js` at startup.

## Features
- Timeline, cut, ripple, reorder, crossfade
- Preview frame, OTIO export, persistent jobs
- 10 plugins, Gremlin bridge (`POST /api/integrate/gremlin`)

See `docs/AGENT_SKILL.md` and `docs/PHASE3.md`.
