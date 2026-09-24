# Install

```bash
git clone https://github.com/enrrutador/ContentGremlin.git
cd ContentGremlin/video_editor
npm install
node server.js
```

http://localhost:3000

Requires Node ≥ 18, ffmpeg, ffprobe.

The full Phase 3 server is stored as `server.payload.{0,1,2,3}.b64` (gzip+base64).
`server.js` joins, decodes, and runs it automatically.
