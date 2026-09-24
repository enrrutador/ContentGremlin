# Install video_editor

```bash
git clone https://github.com/enrrutador/ContentGremlin.git
cd ContentGremlin/video_editor
npm install
node server.js
```

http://localhost:3000

Requires: Node ≥ 18, ffmpeg, ffprobe.

`server.js` decodes `server.payload.b64` (full Phase 3 server, gzip+base64) and runs it.
Optional: set `USE_MONOLITH=1` if you also have `server.monolith.js`.
