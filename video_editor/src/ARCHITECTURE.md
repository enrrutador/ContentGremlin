# Arquitectura del editor

```
server.js
  └─ src/app.js          # Express + rutas (runtime)
       ├─ src/lib/project.js
       ├─ src/lib/media.js
       ├─ ../lib/otio.js
       └─ ../lib/jobs.js
```

`app.js` usa helpers de `lib/`. Siguiente paso: `src/routes/*.js` (projects, timeline, render, agent).

Render: FFmpeg concat/xfade/filtros. Predecible, no NLE pro.
