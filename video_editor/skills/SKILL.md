# Skills — Video Editor local (para agentes)

**Base URL:** `http://127.0.0.1:3000`
**UI:** misma URL en el navegador
**Requisito:** `node server.js` corriendo en `video_editor/`

## Cómo usar estos skills

Leé el skill que corresponda **antes** de llamar endpoints. No inventes paths ni campos.
Si un call falla, leé el JSON `error` + `hint` / `available` y corregí.

## Orden recomendado (primer montaje)

1. `01_project.md` — crear / cargar proyecto
2. `02_import.md` — importar medios
3. `03_timeline.md` — clips, corte, orden
4. `04_effects.md` — fades, blur, crossfade
5. `05_render.md` — exportar MP4
6. `06_gremlin_bridge.md` — traer video desde ContentGremlin

Atajo de alto nivel: `playbook_assemble.md`
Chequeo de estado: `GET /api/agent/status?projectId=...`

## Reglas de oro

- Siempre guardá `projectId` y los `mediaId` / `clipId` de las respuestas.
- No subas videos a servicios externos; todo es local.
- En modo supervisado: mostrá `jobId` y `url` al usuario antes de publicar en YouTube.
- Poll de render: cada 1–2 s hasta `status` = `done` | `error` (máx ~3 min).
- Si FFmpeg falla, el job queda en `error` con mensaje; no reintentes en loop infinito.

## Capacidades

```
GET /api/capabilities
```

## Efectos disponibles

```
GET /api/agent/effects
```
