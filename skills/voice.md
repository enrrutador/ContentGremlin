# Skill: Generate Voice (TTS)

## Goal
Turn the approved script into narration audio (MP3).

## Steps
```json
POST /api/generate_voice
{"text": "<full script>", "title": "<safe name>", "voice": null}
```
Report `audio_path`. If missing API key, tell user to set OPENAI_API_KEY or ElevenLabs.

## Next
→ subtitles / video / super_pipeline
