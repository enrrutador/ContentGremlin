# Video Editor Local MVP

Editor local inspirado en Premiere con API para agente.

## Estructura
- `server.js` API Express con proyectos, importación, timeline y render con FFmpeg.
- `public/index.html` UI mínima: biblioteca, previsualización, timeline multipista.
- `projects/` proyectos guardados en JSON.
- `media/` archivos importados.
- `plugins/` manifiestos de complementos.

## Uso
```bash
cd video_editor
npm install
node server.js
```
Abrir http://localhost:3000

## API
POST /api/projects
POST /api/media/import
POST /api/timeline/clips
POST /api/timeline/cut
POST /api/timeline/effects
POST /api/timeline/transitions
POST /api/render
GET /api/render/{jobId}

## Fases
1. Editor local funcional
2. API agente + guardado
3. Sistema de plugins
4. Catálogo 200 módulos
