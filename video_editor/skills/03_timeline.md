# Skill: Timeline (clips, corte, orden)

Pistas: `v1`, `v2` (video), `a1` (audio).

## Agregar clip

```http
POST /api/timeline/clips
{ "projectId": "...", "trackId": "v1", "mediaId": "..." }
```

Opcional: `"start": 5.0`. Sin start → al final.

## Cortar

```http
POST /api/timeline/cut
{ "projectId": "...", "clipId": "...", "atRelative": 3.5 }
```

`atRelative` = segundos desde el inicio del **clip**.

## Trim

```http
POST /api/timeline/trim
{ "projectId": "...", "clipId": "...", "inPoint": 1.0, "outPoint": 8.0 }
```

## Mover

```http
POST /api/timeline/move
{ "projectId": "...", "clipId": "...", "start": 10.0, "trackId": "v1" }
```

## Borrar (ripple por defecto)

```http
DELETE /api/timeline/clips/{clipId}?projectId=...&ripple=true
```

## Cerrar huecos

```http
POST /api/timeline/ripple
{ "projectId": "...", "trackId": "v1" }
```

## Estado

```http
GET /api/agent/status?projectId=...
```
