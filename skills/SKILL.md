# ContentGremlin — Skill maestro para agentes

**Base URL por defecto:** `http://127.0.0.1:8000`
**Editor local:** `http://127.0.0.1:3000` (ver `editor.md` y `video_editor/skills/`)

Sos un operador de ContentGremlin. **No improvisés el pipeline.** Leé el skill del paso actual y llamá la API. Si falla, leé `detail` / `error` y corregí.

---

## Reglas que no se rompen

1. **Nunca copiar** títulos, guiones, estructura o frases del canal de referencia.
2. Del análisis solo sacás **patrones de alto nivel** (temas, duración, tipo de gancho, ritmo).
3. Respetá el **modo**:
   - `supervised` → mostrá resultado y esperá OK del usuario en: ideas, script, video, upload.
   - `autonomous` → avanzá; **upload** solo si `autonomous_upload_allowed` y `explicit_approval`.
4. Preferí endpoints de la API antes de “inventar” contenido vos mismo.
5. Guardá siempre los IDs y paths que devuelve cada respuesta (`library_id`, `audio_path`, `video_path`, etc.).

---

## Skills por paso (orden de lectura)

| # | Skill | Cuándo |
|---|--------|--------|
| 0 | Este archivo | Arranque |
| 1 | `status_mode.md` | Antes de todo |
| 2 | `analyze.md` | Canal de referencia |
| 3 | `ideas.md` | Generar ángulos originales |
| 4 | `script.md` | Guion completo |
| 5 | `safety.md` | Chequeo de originalidad |
| 6 | `voice.md` | Audio TTS |
| 7 | `subtitles.md` | SRT/VTT |
| 8 | `video.md` | Video simple + audio |
| 9 | `cinematic.md` | Video por escenas |
| 10 | `metadata.md` | Título, descripción, tags |
| 11 | `thumbnail.md` | Miniatura |
| 12 | `super_pipeline.md` | Atajo post-script |
| 13 | `editor.md` | Montaje local |
| 14 | `upload.md` | YouTube (opcional) |
| 15 | `playbook_full.md` | Flujo extremo a extremo |
| 16 | `library.md` | Recuperar corridas previas |

---

## Workflow recomendado (resumen)

```
GET  /api/status
POST /api/set_mode                     { "mode": "supervised" }
POST /api/analyze_channel              { "channel_url": "..." }
POST /api/generate_ideas               { "analysis_report": {...}, "count": 8 }
  → (supervised: usuario elige idea)
POST /api/write_script                 { "idea": {...} }
POST /api/super_pipeline               { "script": "...", "title": "...", "open_in_editor": true }
  → opcional: refinar en editor :3000
POST /api/upload_video                 # solo con permiso + credenciales
```

---

## Endpoints de control

```http
GET  /api/status
GET  /api/mode
POST /api/set_mode
GET  /api/profile
POST /api/profile
GET  /api/config/public
GET  /api/library
GET  /api/agent/skills
```

---

## Errores globales

| Síntoma | Acción |
|---------|--------|
| ECONNREFUSED :8000 | Arrancar API Gremlin |
| ECONNREFUSED :3000 | Arrancar editor (`cd video_editor && node server.js`) |
| 400 + detail | Leer mensaje; faltan campos o LLM/TTS mal configurado |
| 403 en upload | No hay permiso de upload o credenciales |
