# Guía rápida para agentes

Skills detallados en **`video_editor/skills/`**:

| Archivo | Uso |
|---------|-----|
| SKILL.md | Índice y reglas de oro |
| 01_project.md | Crear/cargar proyecto |
| 02_import.md | Importar medios |
| 03_timeline.md | Clips, cut, move, ripple |
| 04_effects.md | Efectos y crossfade |
| 05_render.md | Export y poll |
| 06_gremlin_bridge.md | Desde ContentGremlin |
| playbook_assemble.md | Flujo completo recomendado |

## Atajos

```
GET  /api/capabilities
GET  /api/agent/status?projectId=
GET  /api/agent/effects
POST /api/agent/assemble
POST /api/render  →  GET /api/render/{jobId}
```

Base: `http://127.0.0.1:3000`
