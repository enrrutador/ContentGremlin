# Skill: Analyze Channel

## Goal
Extract **high-level patterns only** from a successful YouTube channel. Never download or copy full content.

## When
User provides a channel URL, handle (`@name`), or says "analyze this channel".

## Steps
1. Normalize input to a YouTube URL if needed (`@handle` → `https://www.youtube.com/@handle`).
2. Call:
   ```json
   POST /api/analyze_channel
   {"channel_url": "<url or handle>"}
   ```
3. Present: channel name, videos analyzed, average duration, top titles (as examples of what works, not to copy), common patterns.
4. In **supervised** mode: ask "¿Usamos este análisis para generar ideas originales?"

## Do NOT
- Copy titles into new videos
- Scrape full transcripts for copying

## Next
→ `skills/ideas.md`
