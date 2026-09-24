# Playbook: montaje rápido extremo a extremo

## 1. Proyecto
`POST /api/projects` `{ "name": "..." }` → projectId

## 2. Importar
`POST /api/media/import-paths` `{ projectId, paths: [...] }` → mediaIds (orden = orden de montaje)

## 3. Ensamblar + render

```http
POST /api/agent/assemble
{
  "projectId": "...",
  "mediaIds": ["id1", "id2", "id3"],
  "crossfade": 1,
  "fadeInFirst": true,
  "width": 1280,
  "height": 720,
  "render": true
}
```

→ jobId. Si solo armar: `"render": false`.

## 4. Poll
`GET /api/render/{jobId}` cada 1–2 s hasta done|error

## 5. Entregar
`http://127.0.0.1:3000` + `url` del job, o `outputPath`

## Si falla
1. `GET /api/agent/status?projectId=`
2. Revisá tips / missing
3. `GET /api/agent/effects`
