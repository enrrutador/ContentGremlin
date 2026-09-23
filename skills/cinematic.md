# Skill: Cinematic mode

## Goal
Richer video: scenes → image/video per scene → motion → narration.

## Requirements
- Image: `OPENAI_API_KEY` + `IMAGE_PROVIDER=openai`
- Optional video: `VIDEO_PROVIDER=generic_http` + `VIDEO_API_URL`
- Without video API → Ken Burns on stills

## Call
```json
POST /api/cinematic_pipeline
{"script": "...", "title": "...", "burn_subtitles": false, "style": "cinematic, natural light"}
```

Check: `GET /api/cinematic/status`

Prefer draft (`/api/super_pipeline`) for previews; cinematic after script approval. Warn about image API cost (1 image/scene).
