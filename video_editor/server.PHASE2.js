#!/usr/bin/env node
// ContentGremlin video_editor Phase 2 — replace server.js with this file (or merge).
// Features: preview frame, move/reorder, ripple delete, xfade render, agent/assemble
// See docs/AGENT_SKILL.md
//
// IMPORTANT: Full implementation is in the local workspace at video_editor/server.js
// This stub documents the new endpoints until the full file is merged:
//
// GET  /api/preview/frame?projectId=&t=
// GET  /api/preview/info?projectId=
// POST /api/timeline/move { projectId, clipId, start? | order[] }
// POST /api/timeline/ripple { projectId, trackId }
// DELETE /api/timeline/clips/:id?projectId=&ripple=true
// POST /api/agent/assemble { projectId, mediaIds[], crossfade, fadeInFirst, width, height }
// Render applies transition.crossfade via ffmpeg xfade between consecutive clips.
console.error('Use server.js from the latest local Phase 2 build, or pull the full server.js commit.');
process.exit(1);
