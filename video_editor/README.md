# Editor local (modular)

```bash
npm install
npm start
```

http://localhost:3000

## Estructura

- `server.js` — entrada
- `src/app.js` — app Express (se crea desde `payload/` en el primer start si no existe)
- `src/config.js`, `src/lib/*` — módulos compartidos
- `lib/otio.js`, `lib/jobs.js` — OTIO y jobs

Skills agentes: `skills/`
