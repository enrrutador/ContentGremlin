# Skill: Super pipeline (post-script)

Una llamada: voz + subtítulos + video + metadata + thumbnail.

```http
POST /api/super_pipeline
Content-Type: application/json

{
  "script": "<guion completo>",
  "title": "ep01-base",
  "voice": null,
  "burn_subtitles": false,
  "open_in_editor": true,
  "idea": { "title": "...", "angle": "..." },
  "template": "dark_minimal"
}
```

## Respuesta

```json
{
  "success": true,
  "audio_path": "...",
  "video_path": "...",
  "srt_path": "...",
  "vtt_path": "...",
  "thumbnail_path": "...",
  "metadata": { },
  "library_id": "...",
  "youtube_configured": false,
  "editor_url": "http://127.0.0.1:3000/?projectId=...",
  "editor_project_id": "...",
  "editor_error": null
}
```

## Después

1. Supervised: mostrar paths + metadata.
2. Si `editor_url`: ofrecer refinar en editor.
3. Upload solo con `upload.md` y permiso.

Editor caído → puede venir `editor_error`; el resto del pack puede estar OK.
