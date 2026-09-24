# YouTube upload (opcional)

## 1. Google Cloud

1. Creá un proyecto en Google Cloud Console
2. Activá **YouTube Data API v3**
3. Credenciales → OAuth client ID (Desktop o Web)
4. Descargá el JSON como `client_secrets.json`

## 2. Colocación

```
credentials/client_secrets.json
```

(o la ruta de `YOUTUBE_CLIENT_SECRETS` en `.env`)

## 3. Primera auth

Al primer `POST /api/upload_video`, se abre el flujo OAuth local y se guarda el token.

## 4. Subir (agente / API)

```http
POST /api/upload_video
{
  "video_path": "/abs/path/video.mp4",
  "title": "...",
  "description": "...",
  "tags": [],
  "privacy": "private",
  "explicit_approval": true
}
```

Sin `explicit_approval` o sin permiso de modo → 403.

Default recomendado: **private** hasta revisión humana.

Ver `skills/upload.md`.
