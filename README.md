# ContentGremlin

**A mischievous little gremlin that studies successful YouTube channels, steals their patterns (never their content), and forges original, high-quality videos for your channel.**

Professional • Agent-friendly • Fully configurable • Runs on localhost

---

## What is ContentGremlin?

ContentGremlin is a powerful, local-first tool designed to help YouTube creators grow faster by analyzing successful channels and generating **100% original** content inspired by their winning patterns.

It does **not** copy videos.  
It studies structure, topics, hooks, pacing and audience signals — then creates something new and better.

### Key Features

- **Full content pipeline**: Analyze → Ideas → Script → Voice → Video → Metadata → Upload
- **Two operating modes**:
  - **Supervised**: You approve every important step
  - **Autonomous**: The gremlin works alone once it knows your style
- **Rich web interface** running on `localhost` with many configuration options, editing capabilities and plugin support
- **Bring your own LLM**: OpenAI, Anthropic, Grok, DeepSeek, Ollama, or any compatible provider
- **YouTube Data API** fully optional (configure when you want)
- **Designed for agents**: Clean REST API + OpenAPI docs so tools like OpenClaw, Hermes and others can use it easily
- **Strong safety layer**: Built-in rules to avoid copyright issues and demonetization risks
- **Extensible**: Plugin system so you can add new capabilities

---

## Philosophy

> "Steal the pattern, not the content."

ContentGremlin is built around three non-negotiable principles:

1. **Originality first** – Every script, title and video must be original.
2. **Human control when needed** – You decide the level of autonomy.
3. **Professional quality** – Clean architecture, excellent documentation, and a serious interface.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/enrrutador/ContentGremlin.git
cd ContentGremlin

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your keys (LLM is required, YouTube is optional)

# Start the gremlin
python main.py
```

Then open your browser at:

**http://localhost:8000**

---

## Interface Overview

The web interface is a first-class citizen of this project. From day one it includes:

| Tab              | Purpose                                      |
|------------------|----------------------------------------------|
| **Dashboard**    | Status, current mode, quick actions, recent activity |
| **Generate**     | Full content creation pipeline with editing at every stage |
| **Configuration**| All settings: LLMs, YouTube, TTS, preferences, mode, advanced parameters |
| **Plugins**      | Install, enable, disable and configure plugins |
| **Library**      | History of ideas, scripts, videos and metadata |
| **Agents & API** | Documentation, API keys, integration examples for OpenClaw, Hermes, etc. |
| **Logs**         | Real-time system logs and diagnostics        |

Everything important can be changed, edited or extended from the interface.

---

## Operating Modes

### Supervised Mode (default)
The gremlin stops at key points and waits for your approval (ideas, script, final video, upload).

### Autonomous Mode
Once you trust it and have configured your style preferences, you can let it run the full pipeline and even upload.

You can switch modes at any time from the interface or via API.

---

## Safety & Anti-Demonetization

ContentGremlin has hard rules that cannot be disabled:

- Never copies scripts, titles or structure literally
- Only extracts high-level patterns
- Forces originality checks
- Encourages unique angles and value
- Never uploads without explicit permission (or Autonomous mode + your prior consent)

The goal is to help you grow **without** risking strikes or demonetization.

---

## For Agents (OpenClaw, Hermes, etc.)

ContentGremlin exposes a clean, well-documented REST API.

- Full OpenAPI documentation available at `/docs` when the server is running
- All major actions are available as endpoints
- Responses are structured JSON
- Designed to be called by other agents without friction

Example tools an agent can use:

- `POST /analyze_channel`
- `POST /generate_ideas`
- `POST /write_script`
- `POST /generate_voice`
- `POST /create_video`
- `POST /upload_video`
- `POST /set_mode`
- `GET  /status`

---

## Configuration

All configuration is available both in the **Configuration** tab of the web interface and via environment variables / config files.

Supported (and planned) providers:

- **LLMs**: OpenAI, Anthropic, xAI/Grok, DeepSeek, Ollama, OpenRouter, etc.
- **YouTube**: Official Data API v3 (optional)
- **TTS**: ElevenLabs, OpenAI TTS, and more
- **Video**: Local FFmpeg + AI tools (extensible via plugins)

---

## Project Status

This repository is under active development.  
We are building a **fully functional** product from the beginning, with a complete interface and solid architecture.

Current focus:
1. Core architecture + configuration system
2. Rich web interface
3. Channel analyzer
4. Idea & script generation with strong originality filters
5. Agent-friendly API
6. Voice, video and upload modules

---

## Contributing

Issues, ideas and pull requests are welcome.  
This is meant to be a serious, useful open-source tool for creators and agent builders.

---

## License

MIT (to be confirmed)

---

**ContentGremlin** — Because sometimes you need a little chaos (and a lot of originality) to grow on YouTube.
