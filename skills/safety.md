# Skill: Seguridad y originalidad

## Report

```http
GET /api/status
```

Incluye bloque `safety`. También `GET /api/safety` si está expuesto.

## Antes de upload

**Nunca** llames `upload_video` sin:

1. OK explícito del usuario en supervised, **o**
2. Autonomous + `autonomous_upload_allowed` + `explicit_approval: true`.

## Si el usuario pide copiar un video

Rechazá y ofrecé ángulos originales.
