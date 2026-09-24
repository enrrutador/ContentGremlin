# ContentGremlin

Toolkit **local** para estudiar patrones públicos de canales de YouTube y generar **contenido original** (ideas, guion, voz, subtítulos, video borrador, metadata), con montaje opcional y upload solo con permiso.

**Estado:** en maduración. Útil como laboratorio para agentes y borradores; **no** es un reemplazo de Premiere ni un generador automático de videos virales.

---

## Qué hace bien hoy

- Pipeline API: analizar → ideas → guion → voz → video plantilla → metadata
- Modos **supervised** / **autonomous** (upload con frenos)
- Skills detallados para agentes (`skills/`)
- Editor local multipista + FFmpeg + API de montaje
- Shell en `localhost:8000` (pipeline + editor embebido + config)

## Qué todavía no cumple como producto cerrado

- El video base es **plantilla + narración**, no cine automático
- El editor es **MVP** (no keyframes pro, no color suite)
- La calidad del guion/ideas depende de **tu LLM** y de revisión humana
- Safety es ayuda técnica, **no** garantía legal anti-strike
- Integración Generar → Editar → Subir funciona, con bordes rough

---

## Arranque

```bash
git clone https://github.com/enrrutador/ContentGremlin.git
cd ContentGremlin
cp .env.example .env
./start.sh
```

| URL | Qué |
|-----|-----|
| http://127.0.0.1:8000 | Shell unificado |
| http://127.0.0.1:8000/docs | OpenAPI |
| http://127.0.0.1:3000 | Editor |

Requisitos: Python 3.10+, Node 18+, FFmpeg.

---

## Docs

| Doc | Contenido |
|-----|-----------|
| [docs/PRODUCT.md](docs/PRODUCT.md) | Expectativas + camino feliz |
| [docs/INSTALL.md](docs/INSTALL.md) | Instalación |
| [docs/YOUTUBE_SETUP.md](docs/YOUTUBE_SETUP.md) | Upload opcional |
| [skills/SKILL.md](skills/SKILL.md) | Agentes (pipeline) |
| [video_editor/skills/SKILL.md](video_editor/skills/SKILL.md) | Agentes (editor) |

---

## Licencia

MIT
