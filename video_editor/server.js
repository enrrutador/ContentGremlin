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

const execFileP = promisify(execFile);
const __dirname = dirname(fileURLToPath(import.meta.url));
const MEDIA_DIR = join(__dirname, "media");
const PROJECTS_DIR = join(__dirname, "projects");
const PUBLIC_DIR = join(__dirname, "public");
const PLUGINS_DIR = join(__dirname, "plugins");
const RENDER_DIR = join(__dirname, "renders");

await Promise.all([MEDIA_DIR, PROJECTS_DIR, PUBLIC_DIR, RENDER_DIR].map((d) => fs.mkdir(d, { recursive: true })));

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
    id: randomUUID(), name,
    media: [],
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
  if (!proj) return res.status(404).json({ error: "Project not found" });
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
    if (!proj) return res.status(404).json({ error: "Project not found", media });
    proj.media.push(media);
    await saveProject(proj);
  }
  res.json(media);
});

app.get("/api/projects/:id/media", async (req, res) => {
  const proj = await readProject(req.params.id);
  if (!proj) return res.status(404).json({ error: "Project not found" });
  res.json({ media: proj.media || [] });
});

app.post("/api/timeline/clips", async (req, res) => {
  const { projectId, trackId = "v1", mediaId, sourcePath, start, inPoint = 0, outPoint, duration, effects = [] } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "Project not found" });
  const track = findTrack(proj, trackId);
  if (!track) return res.status(404).json({ error: "Track not found" });
  let resolvedPath = sourcePath || null;
  let mediaDuration = duration || 0;
  let mediaItem = null;
  if (mediaId) {
    mediaItem = (proj.media || []).find((m) => m.id === mediaId);
    if (!mediaItem) return res.status(404).json({ error: "Media not found in project" });
    resolvedPath = mediaItem.path;
    mediaDuration = mediaItem.duration || 0;
  }
  if (!resolvedPath) return res.status(400).json({ error: "mediaId or sourcePath required" });
  const inPts = Math.max(0, Number(inPoint) || 0);
  let outPts = outPoint != null ? Number(outPoint) : duration != null ? inPts + Number(duration) : mediaDuration || inPts + 5;
  if (mediaDuration > 0) outPts = Math.min(outPts, mediaDuration);
  if (outPts <= inPts) return res.status(400).json({ error: "outPoint must be greater than inPoint" });
  const clip = {
    id: randomUUID(), mediaId: mediaId || null, sourcePath: resolvedPath,
    filename: mediaItem?.filename || basename(resolvedPath),
    start: start != null ? Number(start) : trackEnd(track),
    inPoint: inPts, outPoint: outPts, duration: outPts - inPts,
    effects: Array.isArray(effects) ? effects : [],
  };
  track.clips.push(clip);
  track.clips.sort((a, b) => a.start - b.start);
  await saveProject(proj);
  res.json({ clipId: clip.id, clip });
});

app.post("/api/timeline/cut", async (req, res) => {
  const { projectId, clipId, at, atRelative } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "Project not found" });
  const found = findClip(proj, clipId);
  if (!found) return res.status(404).json({ error: "Clip not found" });
  const { track, clip } = found;
  const cutAt = atRelative != null ? clip.start + Number(atRelative) : Number(at);
  if (!(cutAt > clip.start && cutAt < clip.start + clip.duration)) {
    return res.status(400).json({ error: "Cut point must be inside the clip", clipStart: clip.start, clipEnd: clip.start + clip.duration, cutAt });
  }
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
  if (!proj) return res.status(404).json({ error: "Project not found" });
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

app.delete("/api/timeline/clips/:clipId", async (req, res) => {
  const projectId = req.query.projectId || req.body?.projectId;
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "Project not found" });
  for (const track of proj.timeline.tracks) {
    const i = track.clips.findIndex((c) => c.id === req.params.clipId);
    if (i >= 0) { track.clips.splice(i, 1); await saveProject(proj); return res.json({ ok: true }); }
  }
  res.status(404).json({ error: "Clip not found" });
});

app.post("/api/timeline/effects", async (req, res) => {
  const { projectId, clipId, effectId, params = {} } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "Project not found" });
  const found = findClip(proj, clipId);
  if (!found) return res.status(404).json({ error: "Clip not found" });
  const plugins = await loadPlugins();
  const plugin = plugins.find((p) => p.id === effectId);
  if (!plugin) return res.status(404).json({ error: "Effect plugin not found", available: plugins.map((p) => p.id) });
  found.clip.effects = found.clip.effects || [];
  found.clip.effects.push({ id: randomUUID(), effectId, params: { ...params }, appliedAt: new Date().toISOString() });
  await saveProject(proj);
  res.json({ ok: true, clip: found.clip, plugin: { id: plugin.id, name: plugin.name } });
});

app.post("/api/timeline/transitions", async (req, res) => {
  const { projectId, fromClipId, toClipId, transitionId = "transition.crossfade", duration = 1 } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "Project not found" });
  if (!findClip(proj, fromClipId) || !findClip(proj, toClipId)) return res.status(404).json({ error: "Clip(s) not found" });
  const tr = { id: randomUUID(), transitionId, fromClipId, toClipId, duration: Number(duration) || 1 };
  proj.timeline.transitions = proj.timeline.transitions || [];
  proj.timeline.transitions.push(tr);
  await saveProject(proj);
  res.json({ ok: true, transition: tr });
});

async function renderTimeline(proj, opts = {}) {
  const width = opts.width || 1280, height = opts.height || 720, jobId = opts.jobId || randomUUID();
  const outPath = opts.outputPath || join(RENDER_DIR, `${jobId}.mp4`);
  const vTrack = findTrack(proj, "v1") || proj.timeline.tracks.find((t) => t.type === "video");
  const aTrack = findTrack(proj, "a1") || proj.timeline.tracks.find((t) => t.type === "audio");
  const vClips = [...(vTrack?.clips || [])].sort((a, b) => a.start - b.start);
  if (!vClips.length) throw new Error("No video clips on timeline");
  const tmpDir = join(RENDER_DIR, `tmp_${jobId}`);
  await fs.mkdir(tmpDir, { recursive: true });
  const segmentPaths = [];
  for (let i = 0; i < vClips.length; i++) {
    const clip = vClips[i];
    if (!clip.sourcePath || !existsSync(clip.sourcePath)) throw new Error(`Missing source for clip ${clip.id}`);
    const seg = join(tmpDir, `seg_${String(i).padStart(3, "0")}.mp4`);
    const dur = clip.duration || clip.outPoint - clip.inPoint;
    const vf = [`scale=${width}:${height}:force_original_aspect_ratio=decrease`, `pad=${width}:${height}:(ow-iw)/2:(oh-ih)/2`];
    for (const ef of clip.effects || []) {
      if (ef.effectId === "effect.fade_in") vf.push(`fade=t=in:st=0:d=${ef.params?.duration ?? 1}`);
      else if (ef.effectId === "effect.fade_out") {
        const d = ef.params?.duration ?? 1;
        vf.push(`fade=t=out:st=${Math.max(0, dur - d)}:d=${d}`);
      } else if (ef.effectId === "effect.scale") {
        const z = ef.params?.zoom ?? 1;
        if (z !== 1) vf.push(`scale=iw*${z}:ih*${z}`);
      }
    }
    await execFileP("ffmpeg", ["-y", "-ss", String(clip.inPoint || 0), "-i", clip.sourcePath, "-t", String(dur), "-vf", vf.join(","), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", seg], { maxBuffer: 20e6 });
    segmentPaths.push(seg);
  }
  const listFile = join(tmpDir, "list.txt");
  await fs.writeFile(listFile, segmentPaths.map((p) => `file '${p.replace(/'/g, "'\\''")}'`).join("\n"));
  const silentVideo = join(tmpDir, "video_silent.mp4");
  await execFileP("ffmpeg", ["-y", "-f", "concat", "-safe", "0", "-i", listFile, "-c:v", "libx264", "-pix_fmt", "yuv420p", silentVideo], { maxBuffer: 20e6 });
  const aClips = [...(aTrack?.clips || [])].sort((a, b) => a.start - b.start);
  const audioSources = aClips.length ? aClips : vClips.filter((c) => c.sourcePath);
  let muxed = false;
  if (audioSources.length) {
    const audioSegs = [];
    for (let i = 0; i < audioSources.length; i++) {
      const clip = audioSources[i];
      const seg = join(tmpDir, `aud_${String(i).padStart(3, "0")}.m4a`);
      const dur = clip.duration || clip.outPoint - clip.inPoint;
      const args = ["-y", "-ss", String(clip.inPoint || 0), "-i", clip.sourcePath, "-t", String(dur), "-vn", "-c:a", "aac", "-b:a", "192k"];
      for (const ef of clip.effects || []) {
        if (ef.effectId === "effect.volume") args.push("-af", `volume=${ef.params?.level ?? 1}`);
      }
      args.push(seg);
      try { await execFileP("ffmpeg", args, { maxBuffer: 20e6 }); audioSegs.push(seg); } catch {}
    }
    if (audioSegs.length) {
      const aList = join(tmpDir, "alist.txt");
      await fs.writeFile(aList, audioSegs.map((p) => `file '${p.replace(/'/g, "'\\''")}'`).join("\n"));
      const audioOut = join(tmpDir, "audio.m4a");
      await execFileP("ffmpeg", ["-y", "-f", "concat", "-safe", "0", "-i", aList, "-c:a", "aac", audioOut], { maxBuffer: 20e6 });
      await execFileP("ffmpeg", ["-y", "-i", silentVideo, "-i", audioOut, "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", outPath], { maxBuffer: 20e6 });
      muxed = true;
    }
  }
  if (!muxed) await fs.copyFile(silentVideo, outPath);
  return { outputPath: outPath, segments: segmentPaths.length };
}

app.post("/api/render", async (req, res) => {
  const { projectId, width, height, outputPath } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "Project not found" });
  const jobId = randomUUID();
  db.renders.set(jobId, { status: "queued", projectId, jobId });
  setImmediate(async () => {
    try {
      db.renders.set(jobId, { status: "running", projectId, jobId });
      const result = await renderTimeline(proj, { jobId, width: width || 1280, height: height || 720, outputPath });
      db.renders.set(jobId, { status: "done", jobId, projectId, outputPath: result.outputPath, url: `/renders/${basename(result.outputPath)}`, segments: result.segments });
    } catch (e) {
      db.renders.set(jobId, { status: "error", jobId, projectId, error: String(e.message || e) });
    }
  });
  res.json({ jobId });
});

app.get("/api/render/:jobId", (req, res) => {
  const job = db.renders.get(req.params.jobId);
  if (!job) return res.status(404).json({ error: "Job not found" });
  res.json(job);
});

app.get("/api/plugins", async (_req, res) => {
  const plugins = await loadPlugins();
  res.json({ count: plugins.length, plugins });
});

app.use(express.static(PUBLIC_DIR));
app.get("/", (_req, res) => res.sendFile(join(PUBLIC_DIR, "index.html")));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Editor local en http://localhost:${PORT}`));
