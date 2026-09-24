# Skill: Super Pipeline

## Goal
Script → voice + subs + video + metadata + thumb → optional **open in editor** → optional YouTube upload.

## Call
```json
POST /api/super_pipeline
{
  "script": "...",
  "title": "...",
  "burn_subtitles": false,
  "open_in_editor": true
}
```

## One-click editor
```json
POST /api/open_in_editor
{ "video_path": "/path/out.mp4", "name": "Mi video" }
```

Returns `editor_url` → http://localhost:3000/?projectId=...

Then upload: `skills/upload.md`.
