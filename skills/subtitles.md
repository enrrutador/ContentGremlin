# Skill: Subtitles

## Goal
Generate SRT and VTT from the script.

## Steps
```json
POST /api/generate_subtitles
{"script": "<full script>", "title": "<name>"}
```
Return `srt_path`, `vtt_path`. Ask if user wants burn-in (`burn_subtitles: true` in super_pipeline).
