# Production Engine (v0.3)

Profile-driven pipeline aimed at **publish-ready** videos with minimal intervention.

## Endpoints

| Method | Path | Purpose |
|--------|------|--------|
| GET/POST | `/api/production` | Read/update production profile |
| POST | `/api/produce` | Full produce (B-roll, timeline, subs, music, QA) |
| POST | `/api/produce_async` | Same as job; poll `/api/jobs/{id}` |
| POST | `/api/qa` | Technical QA on an existing MP4 |
| GET | `/api/broll/status` | Pexels/Pixabay + cache |
| GET | `/api/music/status` | Local music library |

Legacy template pipeline remains on `/api/super_pipeline` (when core routes are loaded).

## Production profile

Defaults live in `core/config.py` (`normalize_production`). Configure once per user; the engine never hardcodes niche.

Important keys: `visual_style`, `editing_pace`, `subtitle_style`, `quality_bar`, `broll`, `music`, `target_resolution`, `hook_max_seconds`, `max_silence_seconds`.

## B-roll

Set `PEXELS_API_KEY` and/or `PIXABAY_API_KEY`. Source mode `mixed` tries Pexels then Pixabay. Clips cached under `data/broll/cache/` with relevance scoring (resolution, orientation, duration fit).

## Music

Drop royalty-free tracks in `data/music/` (optional mood subfolders). Ducking uses FFmpeg `sidechaincompress` with volume fallback.

## QA

`modules/qa_agent.py` checks duration, resolution, audio presence, silence, loudness, and hook-window energy. `quality_bar=publishable` requires score ≥ 0.78 and no hard failures.

## Merge note

Feature branch `feat/production-engine-v1` adds production modules and mounts them from `api/routes.py`. When merging to `main`, keep the full legacy `api/routes.py` body from `main` and add:

```python
from api.production_routes import router as production_router
router.include_router(production_router)
```

## Honest limits

Stock query quality depends on scene prompts. Avatar providers are profile-ready but not fully wired. QA is technical, not creative judgment.
