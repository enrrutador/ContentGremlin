# Install

```bash
git clone https://github.com/enrrutador/ContentGremlin.git
cd ContentGremlin/video_editor
npm install
node server.js
```

http://localhost:3000

Requires: Node ≥ 18, ffmpeg, ffprobe.

## How the server loads

`server.js` joins `payload/00.b64` … `22.b64` (gzip+base64 of the full Phase 4 app), decodes, and runs it.

Optional: place `server.monolith.js` and run `USE_MONOLITH=1 node server.js`.

To repack after editing the monolith:

```bash
bash scripts/pack-server.sh
```
