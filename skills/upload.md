# Skill: Subir a YouTube

## Condiciones obligatorias

1. `youtube_configured: true` en `/api/status`
2. Permiso del usuario **o** (autonomous_upload_allowed + explicit_approval)
3. `video_path` existente

Si falta (1): indicar OAuth / client_secrets. Si falta (2): **no llamar**.

## Llamada

```http
POST /api/upload_video
Content-Type: application/json

{
  "video_path": "/abs/path/video.mp4",
  "title": "Título final",
  "description": "Descripción...",
  "tags": ["tag1", "tag2"],
  "privacy": "private",
  "thumbnail_path": "/abs/path/thumb.png",
  "explicit_approval": true
}
```

`privacy`: `private` | `unlisted` | `public`. En supervised default **private**.

## Respuesta OK

```json
{
  "success": true,
  "video_id": "...",
  "url": "https://www.youtube.com/watch?v=...",
  "privacy": "private"
}
```

## Errores

| Código | Significado |
|--------|-------------|
| 403 | Sin approval / política |
| 400 | Path inválido o API Google |

No reintentes en loop si 403. No publiques sin pedido explícito.
