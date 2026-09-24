#!/usr/bin/env node
import express from "express";
import cors from "cors";
import multer from "multer";
import { randomUUID } from "crypto";
import { promises as fs } from "fs";
import { existsSync } from "fs";
import { join, extname, basename } from "path";
import { execFile } from "child_process";
import { promisify } from "util";
import { fileURLToPath } from "url";
import { dirname } from "path";
import { projectToOTIO } from "./lib/otio.js";
import { createJobStore } from "./lib/jobs.js";

const execFileP = promisify(execFile);
const __dirname = dirname(fileURLToPath(import.meta.url));
const MEDIA_DIR = join(__dirname, "media");
const PROJECTS_DIR = join(__dirname, "projects");
const PUBLIC_DIR = join(__dirname, "public");
const PLUGINS_DIR = join(__dirname, "plugins");
const RENDER_DIR = join(__dirname, "renders");
const PREVIEW_DIR = join(RENDER_DIR, "preview");
const JOBS_DIR = join(__dirname, "jobs");
const jobStore = createJobStore(JOBS_DIR);
await Promise.all([MEDIA_DIR, PROJECTS_DIR, PUBLIC_DIR, RENDER_DIR, PREVIEW_DIR, JOBS_DIR].map((d) => fs.mkdir(d, { recursive: true })));

const app = express();
app.use(cors());
app.use(express.json({ limit: "20mb" }));
app.use("/media", express.static(MEDIA_DIR));
app.use("/renders", express.static(RENDER_DIR));

const upload = multer({
  storage: multer.diskStorage({
    destination: (_r, _f, cb) => cb(null, MEDIA_DIR),
    filename: (_r, file, cb) => cb(null, `${randomUUID().slice(0, 8)}${extname(file.originalname) || ".bin"}`),
  }),
  limits: { fileSize: 2 * 1024 * 1024 * 1024 },
});
const db = { projects: new Map(), renders: new Map() };

async function probeMedia(filePath) {
  try {
    const { stdout } = await execFileP("ffprobe", ["-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", filePath], { maxBuffer: 5e6 });
    const info = JSON.parse(stdout);
    const duration = parseFloat(info.format?.duration || 0) || 0;
    const video = (info.streams || []).find((s) => s.codec_type === "video");
    const audio = (info.streams || []).find((s) => s.codec_type === "audio");
    return { duration, width: video?.width || null, height: video?.height || null, hasVideo: !!video, hasAudio: !!audio, codec: video?.codec_name || audio?.codec_name || null };
  } catch (e) {
    return { duration: 0, width: null, height: null, hasVideo: false, hasAudio: false, codec: null, probeError: String(e.message || e) };
  }
}
async function readProject(id) {
  if (db.projects.has(id)) return structuredClone(db.projects.get(id));
  try {
    const proj = JSON.parse(await fs.readFile(join(PROJECTS_DIR, `${id}.json`), "utf-8"));
    db.projects.set(id, proj);
    return structuredClone(proj);
  } catch { return null; }
}
async function saveProject(proj) {
  proj.updatedAt = new Date().toISOString();
  db.projects.set(proj.id, proj);
  await fs.writeFile(join(PROJECTS_DIR, `${proj.id}.json`), JSON.stringify(proj, null, 2));
  return proj;
}
function emptyProject(name = "Untitled") {
  return {
    id: randomUUID(), name, media: [],
    timeline: { tracks: [{ id: "v1", type: "video", clips: [] }, { id: "a1", type: "audio", clips: [] }], transitions: [] },
    createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
  };
}
function findTrack(proj, trackId) { return proj.timeline.tracks.find((t) => t.id === trackId); }
function findClip(proj, clipId) {
  for (const track of proj.timeline.tracks) {
    const clip = track.clips.find((c) => c.id === clipId);
    if (clip) return { track, clip };
  }
  return null;
}
function trackEnd(track) {
  return track.clips.reduce((m, c) => Math.max(m, (c.start || 0) + (c.duration || 0)), 0);
}
function rippleClose(track) {
  const sorted = [...track.clips].sort((a, b) => a.start - b.start);
  let t = 0;
  for (const c of sorted) { c.start = t; t += c.duration || 0; }
  track.clips = sorted;
}
function rippleDelete(track, removedStart, removedDuration) {
  for (const c of track.clips) {
    if (c.start >= removedStart + removedDuration - 1e-6) c.start = Math.max(0, c.start - removedDuration);
  }
  track.clips.sort((a, b) => a.start - b.start);
}
async function loadPlugins() {
  const plugins = [];
  try {
    for (const f of await fs.readdir(join(PLUGINS_DIR, "examples"))) {
      if (!f.endsWith(".json")) continue;
      try { plugins.push(JSON.parse(await fs.readFile(join(PLUGINS_DIR, "examples", f), "utf-8"))); } catch {}
    }
  } catch {}
  return plugins;
}
function resolveClipAtTime(vClips, t) {
  for (const c of vClips) {
    if (t >= c.start && t < c.start + c.duration) return { clip: c, sourceTime: c.inPoint + (t - c.start) };
  }
  if (vClips.length) {
    const last = vClips[vClips.length - 1];
    if (t >= last.start) return { clip: last, sourceTime: last.outPoint - 0.04 };
  }
  return null;
}

app.post("/api/projects", async (req, res) => {
  const project = emptyProject(req.body?.name || "Untitled");
  await saveProject(project);
  res.json({ id: project.id, project });
});
app.get("/api/projects", async (_req, res) => {
  const list = [];
  for (const f of await fs.readdir(PROJECTS_DIR)) {
    if (!f.endsWith(".json")) continue;
    try {
      const p = JSON.parse(await fs.readFile(join(PROJECTS_DIR, f), "utf-8"));
      list.push({ id: p.id, name: p.name, mediaCount: p.media?.length || 0, updatedAt: p.updatedAt });
    } catch {}
  }
  res.json({ projects: list });
});
app.get("/api/projects/:id", async (req, res) => {
  const proj = await readProject(req.params.id);
  if (!proj) return res.status(404).json({ error: "no project" });
  res.json(proj);
});
app.delete("/api/projects/:id", async (req, res) => {
  db.projects.delete(req.params.id);
  try { await fs.unlink(join(PROJECTS_DIR, `${req.params.id}.json`)); } catch {}
  res.json({ ok: true });
});

app.post("/api/media/import", upload.single("file"), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: "No file" });
  const projectId = req.body?.projectId || req.query?.projectId;
  const meta = await probeMedia(req.file.path);
  const media = {
    id: randomUUID(), filename: req.file.originalname, storedName: basename(req.file.path),
    path: req.file.path, url: `/media/${basename(req.file.path)}`, size: req.file.size,
    duration: meta.duration, width: meta.width, height: meta.height,
    hasVideo: meta.hasVideo, hasAudio: meta.hasAudio, codec: meta.codec,
    importedAt: new Date().toISOString(),
  };
  if (projectId) {
    const proj = await readProject(projectId);
    if (!proj) return res.status(404).json({ error: "no project", media });
    proj.media.push(media);
    await saveProject(proj);
  }
  res.json(media);
});
app.get("/api/projects/:id/media", async (req, res) => {
  const proj = await readProject(req.params.id);
  if (!proj) return res.status(404).json({ error: "no project" });
  res.json({ media: proj.media || [] });
});

app.post("/api/timeline/clips", async (req, res) => {
  const { projectId, trackId = "v1", mediaId, sourcePath, start, inPoint = 0, outPoint, duration, effects = [] } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const track = findTrack(proj, trackId);
  if (!track) return res.status(404).json({ error: "Track not found" });
  let resolvedPath = sourcePath || null, mediaDuration = duration || 0, mediaItem = null;
  if (mediaId) {
    mediaItem = (proj.media || []).find((m) => m.id === mediaId);
    if (!mediaItem) return res.status(404).json({ error: "media missing" });
    resolvedPath = mediaItem.path; mediaDuration = mediaItem.duration || 0;
  }
  if (!resolvedPath) return res.status(400).json({ error: "mediaId or sourcePath required" });
  const inPts = Math.max(0, Number(inPoint) || 0);
  let outPts = outPoint != null ? Number(outPoint) : duration != null ? inPts + Number(duration) : mediaDuration || inPts + 5;
  if (mediaDuration > 0) outPts = Math.min(outPts, mediaDuration);
  if (outPts <= inPts) return res.status(400).json({ error: "invalid range" });
  const clip = {
    id: randomUUID(), mediaId: mediaId || null, sourcePath: resolvedPath,
    filename: mediaItem?.filename || basename(resolvedPath),
    start: start != null ? Number(start) : trackEnd(track),
    inPoint: inPts, outPoint: outPts, duration: outPts - inPts,
    effects: Array.isArray(effects) ? effects : [],
  };
  track.clips.push(clip); track.clips.sort((a, b) => a.start - b.start);
  await saveProject(proj);
  res.json({ clipId: clip.id, clip });
});

app.post("/api/timeline/cut", async (req, res) => {
  const { projectId, clipId, at, atRelative } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const found = findClip(proj, clipId);
  if (!found) return res.status(404).json({ error: "Clip not found" });
  const { track, clip } = found;
  const cutAt = atRelative != null ? clip.start + Number(atRelative) : Number(at);
  if (!(cutAt > clip.start && cutAt < clip.start + clip.duration))
    return res.status(400).json({ error: "cut out of range" });
  const sourceCut = clip.inPoint + (cutAt - clip.start);
  const left = { ...clip, outPoint: sourceCut, duration: sourceCut - clip.inPoint };
  const right = { ...clip, id: randomUUID(), start: cutAt, inPoint: sourceCut, outPoint: clip.outPoint, duration: clip.outPoint - sourceCut, effects: [...(clip.effects || [])] };
  const idx = track.clips.findIndex((c) => c.id === clipId);
  track.clips.splice(idx, 1, left, right);
  await saveProject(proj);
  res.json({ ok: true, left, right });
});

app.post("/api/timeline/trim", async (req, res) => {
  const { projectId, clipId, inPoint, outPoint, start, duration } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const found = findClip(proj, clipId);
  if (!found) return res.status(404).json({ error: "Clip not found" });
  const { clip } = found;
  if (inPoint != null) clip.inPoint = Math.max(0, Number(inPoint));
  if (outPoint != null) clip.outPoint = Number(outPoint);
  if (start != null) clip.start = Number(start);
  if (duration != null) { clip.duration = Number(duration); clip.outPoint = clip.inPoint + clip.duration; }
  else clip.duration = clip.outPoint - clip.inPoint;
  if (clip.duration <= 0) return res.status(400).json({ error: "Invalid trim" });
  await saveProject(proj);
  res.json({ ok: true, clip });
});

app.post("/api/timeline/move", async (req, res) => {
  const { projectId, clipId, start, order, pack = false } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const found = findClip(proj, clipId);
  if (!found) return res.status(404).json({ error: "Clip not found" });
  const { track, clip } = found;
  if (Array.isArray(order)) {
    const map = new Map(track.clips.map((c) => [c.id, c]));
    const next = []; let t = 0;
    for (const id of order) {
      const c = map.get(id); if (!c) continue;
      c.start = t; t += c.duration || 0; next.push(c); map.delete(id);
    }
    for (const c of map.values()) { c.start = t; t += c.duration || 0; next.push(c); }
    track.clips = next;
  } else if (start != null) {
    clip.start = Math.max(0, Number(start));
