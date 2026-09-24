import { randomUUID } from "crypto";
import { promises as fs } from "fs";
import { join } from "path";
import { PROJECTS_DIR } from "../config.js";

export const db = { projects: new Map(), renders: new Map() };

export function emptyProject(name = "Untitled") {
  return {
    id: randomUUID(),
    name,
    media: [],
    timeline: {
      tracks: [
        { id: "v1", type: "video", clips: [] },
        { id: "v2", type: "video", clips: [] },
        { id: "a1", type: "audio", clips: [] },
      ],
      transitions: [],
    },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

export async function readProject(id) {
  if (db.projects.has(id)) return structuredClone(db.projects.get(id));
  try {
    const proj = JSON.parse(await fs.readFile(join(PROJECTS_DIR, `${id}.json`), "utf-8"));
    db.projects.set(id, proj);
    return structuredClone(proj);
  } catch {
    return null;
  }
}

export async function saveProject(proj) {
  proj.updatedAt = new Date().toISOString();
  db.projects.set(proj.id, proj);
  await fs.writeFile(join(PROJECTS_DIR, `${proj.id}.json`), JSON.stringify(proj, null, 2));
  return proj;
}

export function findTrack(proj, trackId) {
  return proj.timeline.tracks.find((t) => t.id === trackId);
}

export function findClip(proj, clipId) {
  for (const track of proj.timeline.tracks) {
    const clip = track.clips.find((c) => c.id === clipId);
    if (clip) return { track, clip };
  }
  return null;
}

export function trackEnd(track) {
  return track.clips.reduce((m, c) => Math.max(m, (c.start || 0) + (c.duration || 0)), 0);
}

export function rippleClose(track) {
  const sorted = [...track.clips].sort((a, b) => a.start - b.start);
  let t = 0;
  for (const c of sorted) {
    c.start = t;
    t += c.duration || 0;
  }
  track.clips = sorted;
}

export function rippleDelete(track, removedStart, removedDuration) {
  for (const c of track.clips) {
    if (c.start >= removedStart + removedDuration - 1e-6) {
      c.start = Math.max(0, c.start - removedDuration);
    }
  }
  track.clips.sort((a, b) => a.start - b.start);
}

export function resolveClipAtTime(vClips, t) {
  for (const c of vClips) {
    const end = c.start + c.duration;
    if (t >= c.start && t < end) {
      return { clip: c, sourceTime: c.inPoint + (t - c.start) };
    }
  }
  if (vClips.length) {
    const last = vClips[vClips.length - 1];
    if (t >= last.start) return { clip: last, sourceTime: last.outPoint - 0.04 };
  }
  return null;
}
