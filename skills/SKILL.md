# ContentGremlin — Agent Skill

**You are operating ContentGremlin**, a local tool that analyzes successful YouTube channels and produces **100% original** content (ideas, scripts, voice, subtitles, video, metadata, thumbnails) without copying.

You are **not** a YouTube expert by default. Follow this skill exactly. Do not invent your own pipeline.

---

## Core rules (never break)

1. **Never copy** titles, scripts, structure, or wording from the reference channel.
2. Only extract **high-level patterns** (topics, length, hook style, pacing).
3. Respect **mode**:
   - `supervised` → ask the user before ideas, script, video, upload.
   - `autonomous` → proceed, but **upload** still needs prior permission (`autonomous_upload_allowed`).
4. Prefer calling ContentGremlin API endpoints over doing the work yourself.
5. Base URL (default): `http://localhost:8000`

---

## Recommended full workflow

```
1. GET  /api/status
2. POST /api/analyze_channel
3. POST /api/generate_ideas
4. POST /api/write_script
5. POST /api/super_pipeline
6. POST /api/upload_video (only if allowed)
```

In **supervised** mode: after analysis, ideas, script and before upload, **stop and show results to the user** for approval.

---

## Capability skills

| Skill file | When to use |
|------------|-------------|
| `skills/analyze.md` | User gives a channel URL / handle |
| `skills/ideas.md` | After analysis, need original video ideas |
| `skills/script.md` | User approved an idea |
| `skills/voice.md` | Script ready → narration |
| `skills/subtitles.md` | Need SRT/VTT |
| `skills/metadata.md` | Title, description, tags, chapters |
| `skills/thumbnail.md` | Cover image |
| `skills/video.md` | Assemble video |
| `skills/upload.md` | Publish to YouTube |
| `skills/super_pipeline.md` | One-shot production from script |
| `skills/safety.md` | Always active constraints |

Interactive docs: `http://localhost:8000/docs`
Fetch all skills: `GET /api/agent/skills`
