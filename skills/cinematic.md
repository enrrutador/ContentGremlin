# Skill: Pipeline cinemático

## Estado

```http
GET /api/cinematic/status
```

## Llamada

```http
POST /api/cinematic_pipeline
Content-Type: application/json

{
  "script": "...",
  "title": "ep01",
  "voice": null,
  "burn_subtitles": false,
  "style": "cinematic dark"
}
```

Guardá `video_path`. Si no hay image/video gen, el sistema puede degradar; no prometas providers no configurados.
