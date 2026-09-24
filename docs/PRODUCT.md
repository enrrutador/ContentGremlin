# ContentGremlin — camino a producto

## Qué es

Toolkit **local** para analizar patrones de un canal, generar idea → guion → voz → video borrador → metadata, montar en editor local y subir a YouTube solo con permiso.

## Arranque

```bash
git clone https://github.com/enrrutador/ContentGremlin.git
cd ContentGremlin
cp .env.example .env
./start.sh
```

- API: http://127.0.0.1:8000
- Editor: http://127.0.0.1:3000

Requisitos: Python 3.10+, Node 18+, FFmpeg.

## Camino feliz

1. `GET /api/status`
2. `POST /api/set_mode` `{ "mode": "supervised" }`
3. `POST /api/analyze_channel` `{ "channel_url": "..." }`
4. `POST /api/generate_ideas` → elegir idea
5. `POST /api/write_script`
6. `POST /api/super_pipeline` `{ "script", "title", "open_in_editor": true }`
7. Abrir `editor_url` o usar `video_path`

Skills: `skills/playbook_full.md`

## Flujo unificado

Generar (:8000) → Montar (:3000) → Export MP4 → Upload opcional

## Config

| Qué | Dónde |
|-----|--------|
| LLM/TTS | `.env` + `/api/profile` |
| YouTube | client_secrets + `skills/upload.md` |
| Editor | `video_editor/server.monolith.js` |

## Qué no promete

Premiere completo; cinemático sin providers; autopublicar sin confirmación.
