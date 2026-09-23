# ContentGremlin

**Local toolkit that studies public patterns from successful YouTube channels and helps you generate original ideas, scripts, voice, subtitles, metadata and simple videos — without copying content.**

Agent-friendly • Configurable • Runs on localhost • Early but usable

---

## What is ContentGremlin?

ContentGremlin is a **local-first MVP** to help creators:

1. Analyze public metadata from a reference channel (titles, lengths, title formulas)
2. Generate **original** ideas and scripts via your LLM
3. Produce narration, subtitles, metadata, thumbnails and a **simple template video**
4. Optionally upload with explicit permission

It does **not** magically produce cinematic YouTube videos. Current video output is a polished still-template + voice (good for drafts / faceless starters), not a full editor replacement.

Originality checks use multi-signal text similarity (Jaccard, LCS, n-grams). Human review is still recommended before publishing.

### Key Features

- Full content pipeline: Analyze → Ideas → Script → Voice → Video → Metadata → Upload
- Modes: **Supervised** (approve steps) and **Autonomous** (with upload gates)
- Web UI on `localhost`
- Bring your own LLM (OpenAI, Anthropic, xAI, Ollama, …)
- YouTube Data API optional
- Agent skills + `GET /api/agent/skills`
- Safety layer with multi-signal originality checks (not a legal guarantee)
- Minimal plugin loader under `plugins/`

---

## Quick Start

```bash
git clone https://github.com/enrrutador/ContentGremlin.git
cd ContentGremlin
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add at least one LLM key
python main.py
```

Open **http://localhost:8000**

Tests: `python tests/test_safety.py` and `python tests/test_subtitles.py`

---

## For agents

See `docs/AGENTS.md`, `skills/SKILL.md`, and `GET /api/agent/skills`.

---

## License

MIT
