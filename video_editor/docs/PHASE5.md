# Phase 5 — Premiere light + Gremlin bridge

## Editor
- Pista **v2**
- Proxies `POST /api/media/proxy`
- Keyframes opacity `POST /api/timeline/keyframes`
- GPU opcional `useHwAccel` (NVENC si hay)
- `GET /api/capabilities`

## Gremlin ↔ Editor
- `POST /api/super_pipeline` + `open_in_editor: true`
- `POST /api/open_in_editor` `{ video_path, name }`
- Deep link `http://localhost:3000/?projectId=...`

## Pipeline YouTube
analyze → script → super_pipeline → editor → upload_video
