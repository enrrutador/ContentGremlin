# ContentGremlin for Agents (OpenClaw, Hermes, Cursor, etc.)

ContentGremlin is **agent-first**: a non-expert LLM can run a full YouTube production pipeline by following the skills in this repo.

## Quick start for agents

1. Run the server: `python main.py` → `http://localhost:8000`
2. Load system prompt: `prompts/agent_system.md`
3. Load master skill: `skills/SKILL.md`
4. Use capability skills under `skills/` as needed

Or fetch everything:

```http
GET http://localhost:8000/api/agent/skills
```

## Why skills exist

The user's LLM is **not** assumed to be an expert in YouTube SEO, retention, TTS, or FFmpeg.
The skills encode the expert workflow so the agent only needs to **call the right endpoints in the right order**.

## Capability map

| Step | Skill file | Endpoint |
|------|------------|----------|
| Analyze channel | `skills/analyze.md` | `POST /api/analyze_channel` |
| Original ideas | `skills/ideas.md` | `POST /api/generate_ideas` |
| Script | `skills/script.md` | `POST /api/write_script` |
| Voice | `skills/voice.md` | `POST /api/generate_voice` |
| Subtitles | `skills/subtitles.md` | `POST /api/generate_subtitles` |
| Metadata | `skills/metadata.md` | `POST /api/generate_metadata` |
| Thumbnail | `skills/thumbnail.md` | `POST /api/generate_thumbnail` |
| Video | `skills/video.md` | `POST /api/create_video` or `full_pipeline` |
| Full production | `skills/super_pipeline.md` | `POST /api/super_pipeline` |
| Upload | `skills/upload.md` | `POST /api/upload_video` |
| Safety | `skills/safety.md` | always |

## Modes

- **Supervised**: pause for approval after analysis, ideas, script, and before upload.
- **Autonomous**: chain steps; upload still needs `autonomous_upload_allowed` or explicit approval.

`POST /api/set_mode` with `{"mode": "supervised"|"autonomous"}`.

## Example supervised session

```
1. GET /api/status
2. POST /api/analyze_channel
3. Show report → user OK
4. POST /api/generate_ideas
5. User picks idea
6. POST /api/write_script
7. User approves script
8. POST /api/super_pipeline
9. User reviews assets
10. POST /api/upload_video (explicit_approval: true)
```

## Integration

- **OpenClaw / Hermes**: register HTTP tools for endpoints; attach `prompts/agent_system.md` + `skills/SKILL.md`.
- **Cursor**: open the `skills/` folder as context.
- **Custom agents**: `GET /api/agent/skills` at startup.

OpenAPI: http://localhost:8000/docs
