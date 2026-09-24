# ContentGremlin

**Toolkit local** para estudiar patrones públicos de canales de YouTube y generar **contenido original** (ideas, guion, voz, subtítulos, video borrador, metadata) — sin copiar.

Agent-friendly · Localhost · Modos supervised/autonomous · Editor de montaje incluido

---

## Qué es

1. Analizar un canal de referencia (patrones, no copias)
2. Generar idea → guion → voz → video → metadata
3. Montar/refinar en el **editor local** (`localhost:3000`)
4. Subir a YouTube solo con permiso explícito

No reemplaza Premiere ni garantiza videos virales. El video base es plantilla + voz (drafts); el editor permite montaje real con FFmpeg.

---

## Arranque (producto)

```bash
git clone https://github.com/enrrutador/ContentGremlin.git
cd ContentGremlin
cp .env.example .env    # LLM / TTS keys
./start.sh              # API + Editor juntos
```

| Servicio | URL |
|----------|-----|
| Gremlin API | http://127.0.0.1:8000 |
| OpenAPI | http://127.0.0.1:8000/docs |
| Editor de video | http://127.0.0.1:3000 |

Requisitos: **Python 3.10+**, **Node 18+**, **FFmpeg**.

### Solo una pieza

```bash
# API
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && python main.py

# Editor
cd video_editor && npm install && npm start
```

---

## Documentación

| Doc | Contenido |
|-----|-----------|
| [docs/PRODUCT.md](docs/PRODUCT.md) | Camino feliz a primer MP4 |
| [docs/INSTALL.md](docs/INSTALL.md) | Instalación |
| [docs/YOUTUBE_SETUP.md](docs/YOUTUBE_SETUP.md) | Upload opcional |
| [skills/SKILL.md](skills/SKILL.md) | Skills para agentes (pipeline) |
| [video_editor/skills/SKILL.md](video_editor/skills/SKILL.md) | Skills del editor |

---

## Features

- Pipeline completo Analyze → Upload
- Modos **Supervised** / **Autonomous** (upload con gates)
- BYO LLM (OpenAI, Anthropic, xAI, Ollama, …)
- Editor local multipista + API para agentes
- YouTube Data API opcional
- Safety multi-señal (no es garantía legal)

---

## License

MIT
