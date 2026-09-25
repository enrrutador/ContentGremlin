# Arquitectura del editor

```
server.js
  └─ src/app.js
       ├─ routes/projects.js
       ├─ routes/media.js
       ├─ routes/timeline.js
       ├─ routes/preview.js
       ├─ routes/render.js
       ├─ routes/agent.js
       ├─ lib/project.js
       ├─ lib/media.js
       ├─ lib/render.js
       ├─ ../lib/otio.js
       └─ ../lib/jobs.js
```

## Render endurecido

- Valida clips (path, duración)
- Límite ~4h de timeline
- Limpia tmp al terminar o fallar
- Hints en errores FFmpeg
- Jobs: queued → running → done|error

## Extender

`export function registerFoo(app, ctx)` en `routes/foo.js` y registrarlo en `app.js`.
