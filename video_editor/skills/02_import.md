# Skill: Importar medios

## Desde archivo (multipart)

```http
POST /api/media/import
Content-Type: multipart/form-data

file: <binario>
projectId: <uuid>
```

**Respuesta tipica:** `{ "id": "<mediaId>", "filename": "...", "duration": 12.5, "path": "...", "url": "/media/..." }`

Guardá `id` y `duration`.

## Desde rutas absolutas del disco (agente / Gremlin)

```http
POST /api/media/import-paths
Content-Type: application/json

{
  "projectId": "<uuid>",
  "paths": ["/home/user/out/clip1.mp4", "/home/user/out/clip2.mp4"]
}
```

Los paths deben existir en la **máquina donde corre el editor**.

## Proxy (opcional)

```http
POST /api/media/proxy
{ "projectId": "...", "mediaId": "...", "width": 640 }
```

## Listar

```http
GET /api/projects/{projectId}/media
```

## Checklist

- [ ] projectId válido
- [ ] al menos 1 mediaId
- [ ] duration > 0
