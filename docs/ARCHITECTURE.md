# ContentGremlin – Architecture

## High-level Overview

ContentGremlin is a modular, local-first application built with:

- **Backend**: FastAPI (Python)
- **Frontend**: Modern web interface (served by FastAPI)
- **Configuration**: Flexible (UI + .env + JSON profiles)
- **Extensibility**: Plugin system
- **Agent compatibility**: Clean REST API + OpenAPI

## Core Principles

1. **Separation of concerns** – Analysis, generation, voice, video, upload and UI are clearly separated.
2. **Provider agnostic** – LLMs, TTS and other services are interchangeable.
3. **Safety by design** – Anti-copy and anti-demonetization rules are enforced at the core level.
4. **Human-in-the-loop when desired** – Supervised vs Autonomous modes.
5. **Rich interface first** – The UI is not an afterthought.

## Main Modules

```
contentgremlin/
├── api/                 # FastAPI routers and endpoints
├── core/                # Mode manager, profile, safety rules, config
├── providers/           # LLM, TTS, YouTube, etc. (pluggable)
├── modules/             # Business logic
│   ├── analyzer.py
│   ├── idea_generator.py
│   ├── script_writer.py
│   ├── voice.py
│   ├── video.py
│   ├── metadata.py
│   └── uploader.py
├── plugins/             # User and community plugins
├── ui/                  # Frontend assets and templates
├── data/                # Local storage (profiles, history, etc.)
└── main.py
```

## Data Flow (Simplified)

1. User (or agent) requests analysis of a reference channel.
2. Analyzer extracts high-level patterns (never raw content).
3. Idea Generator creates original ideas based on patterns + user niche + originality filters.
4. Script Writer produces a full original script.
5. Voice & Video modules turn the script into a finished video.
6. Metadata module creates titles, descriptions, tags and thumbnails.
7. Uploader (optional) publishes to YouTube only when allowed.

In **Supervised** mode the process pauses for human approval at critical steps.  
In **Autonomous** mode it continues according to the user profile.

## Safety Layer

Located in `core/safety.py`. This layer cannot be disabled. It enforces:

- No literal copying of scripts or titles
- Originality scoring
- Pattern-only analysis
- Upload permission checks

## Configuration System

All settings are available in the **Configuration** tab of the web UI and can also be managed via:

- Environment variables (`.env`)
- JSON profile files
- API endpoints

The system supports multiple LLM providers simultaneously and lets the user choose which one to use per task if desired.
