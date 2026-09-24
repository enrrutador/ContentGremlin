# Install video_editor

```bash
git clone https://github.com/enrrutador/ContentGremlin.git
cd ContentGremlin/video_editor
npm install
# Ensure server.monolith.js exists (full Phase 3 server).
# server.js will load it automatically.
node server.js
```

Open http://localhost:3000

If `server.monolith.js` is missing, copy it from a local build or open an issue.
The repo entrypoint is `server.js` → prefers `server.monolith.js`.

## Required
- Node ≥ 18
- ffmpeg + ffprobe on PATH
