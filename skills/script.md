# Skill: Write Script

## Goal
Write a full, original spoken script ready for TTS.

## When
User approved (or autonomous selected) one idea with title, angle, hook.

## Steps
1. Call:
   ```json
   POST /api/write_script
   {"idea": {"title": "...", "angle": "...", "hook": "...", "estimated_minutes": 8}, "language": "es"}
   ```
2. Show script in supervised mode; allow edits.

## Structure
Hook → promise → development → examples → CTA

## Next
→ `skills/super_pipeline.md` (recommended)
