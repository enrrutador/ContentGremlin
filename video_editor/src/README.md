# Editor source

| File | Role |
|------|------|
| `app.js` | Runtime Express app (generated from payload on first clone if missing) |
| `config.js` | Paths |
| `lib/project.js` | Projects + timeline helpers |
| `lib/media.js` | ffprobe, plugins, encoder |
| `index.js` | Re-export entry |

`server.js` → `scripts/ensure-app.mjs` (si falta app.js) → `src/app.js`.

El payload es solo bootstrap; el código de trabajo es `src/app.js` + libs.
