# Skill: Subtítulos

```http
POST /api/generate_subtitles
Content-Type: application/json

{
  "script": "<texto>",
  "title": "ep01",
  "audio_path": "/abs/path/audio.wav"
}
```

## Respuesta

```json
{ "success": true, "srt_path": "...", "vtt_path": "...", "library_id": "..." }
```

Burn-in: en `super_pipeline` / `create_video` con `"burn_subtitles": true`.
