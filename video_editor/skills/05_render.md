# Skill: Render / export

## Iniciar

```http
POST /api/render
{
  "projectId": "...",
  "width": 1280,
  "height": 720,
  "useHwAccel": false
}
```

→ `{ "jobId": "..." }`

## Poll

```http
GET /api/render/{jobId}
```

Estados: `queued` → `running` → `done` | `error`

Cuando `done`: `url` (relativo) y `outputPath` (absoluto).

## Listar jobs

```http
GET /api/render
```

## Preview

```http
POST /api/preview/montage
{ "projectId": "..." }

GET /api/preview/frame?projectId=...&t=2.5
```

## Política del agente

1. No digas listo hasta `status === "done"`.
2. Si `error`, mostrá el mensaje; no loops agresivos.
3. `useHwAccel: true` solo si el usuario pidió GPU; si falla, reintentá con `false`.
4. Supervisado: mostrá URL del MP4 antes de upload YouTube.
