# Skill: Video (plantilla + audio)

## Prerrequisitos

`script` + `audio_path`.

```http
POST /api/create_video
Content-Type: application/json

{
  "script": "...",
  "audio_path": "/abs/path/audio.wav",
  "title": "ep01",
  "burn_subtitles": false,
  "template": "dark_minimal"
}
```

## Respuesta

```json
{ "success": true, "video_path": "/abs/path/video.mp4", "library_id": "..." }
```

Para escenas/motion → `cinematic.md`. Preferí `super_pipeline` post-script.
