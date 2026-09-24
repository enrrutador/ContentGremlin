# Instalación

## Rápida

```bash
git clone https://github.com/enrrutador/ContentGremlin.git
cd ContentGremlin
cp .env.example .env
# Editá OPENAI_API_KEY u otro LLM
./start.sh
```

| Servicio | URL |
|----------|-----|
| Gremlin API | http://127.0.0.1:8000 |
| OpenAPI | http://127.0.0.1:8000/docs |
| Editor | http://127.0.0.1:3000 |

## Requisitos

- Python 3.10+
- Node.js 18+
- FFmpeg + ffprobe en PATH

## Solo una pieza

```bash
# API
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && python main.py

# Editor
cd video_editor && npm install && npm start
```

## Docker (experimental)

```bash
docker compose up
```

## Después de instalar

1. [PRODUCT.md](PRODUCT.md) — camino feliz
2. [skills/SKILL.md](../skills/SKILL.md) — agentes
3. [YOUTUBE_SETUP.md](YOUTUBE_SETUP.md) — upload opcional
