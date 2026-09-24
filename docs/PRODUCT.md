# ContentGremlin — producto

## Arranque

```bash
./start.sh
```

| URL | Qué |
|-----|-----|
| http://127.0.0.1:8000 | **Shell unificado** (pipeline + editor embebido + config) |
| http://127.0.0.1:3000 | Editor directo |
| http://127.0.0.1:8000/docs | OpenAPI |

## Editor — código legible

Al arrancar, `server.js`:

1. Si existe `source/*.js` → ensambla `server.monolith.js`
2. Si no, usa `server.monolith.js` si está
3. Si no, **desempaqueta `payload/*.b64`** → escribe `server.monolith.js` y lo carga

En un clone fresco el payload genera el monolito la primera vez. Después trabajás sobre el `.js` generado.

## Flujo en la UI

Inicio → Pipeline (analizar → ideas → script → super pipeline) → Editor (iframe) → Upload opcional

## Agentes

`skills/playbook_full.md` + `video_editor/skills/playbook_assemble.md`
