# Skill: Proyecto

## Crear

```http
POST /api/projects
Content-Type: application/json

{ "name": "ep01-mi-video" }
```

**Respuesta:** `{ "id": "<projectId>", "name": "...", "media": [], "timeline": { "tracks": [...] } }`

Guardá `id` como `projectId`.

## Cargar / listar

```http
GET /api/projects
GET /api/projects/{projectId}
GET /api/agent/status?projectId={projectId}
```

`/api/agent/status` devuelve resumen legible: medios, clips por pista, duración total, tips.

## Borrar

```http
DELETE /api/projects/{projectId}
```

## Errores comunes

| Código | Causa | Qué hacer |
|--------|--------|-----------|
| 404 | projectId inválido | Crear de nuevo o listar proyectos |
| ECONNREFUSED | server caído | Arrancar `node server.js` en video_editor |
