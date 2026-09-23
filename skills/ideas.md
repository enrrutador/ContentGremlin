# Skill: Generate Original Ideas

## Goal
Produce **original** video ideas inspired by patterns, never clones.

## When
You already have an `analysis_report` from `/api/analyze_channel`.

## Steps
1. Call:
   ```json
   POST /api/generate_ideas
   {"analysis_report": { ... }, "count": 6, "niche": "optional"}
   ```
2. Show each idea: title, angle, hook, why_it_works, estimated_minutes.
3. Supervised: ask user to pick one. Autonomous: pick strongest angle + curiosity.

## Quality bar
Angle must be a **new twist**, not a rephrase of a top video.

## Next
→ `skills/script.md`
