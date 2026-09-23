# Skill: Super Pipeline

## Goal
One call: script → voice + subtitles + video + metadata + thumbnail.

## Steps
```json
POST /api/super_pipeline
{
  "script": "...",
  "title": "...",
  "voice": null,
  "burn_subtitles": false,
  "idea": {"title": "...", "angle": "..."}
}
```
Present all paths + metadata, then offer upload.
