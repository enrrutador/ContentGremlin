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
const PREVIEW_DIR = join(RENDER_DIR, "preview");
await Promise.all([MEDIA_DIR, PROJECTS_DIR, PUBLIC_DIR, RENDER_DIR, PREVIEW_DIR].map((d) => fs.mkdir(d, { recursive: true })));

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
    track.clips.sort((a, b) => a.start - b.start);
    if (pack) rippleClose(track);
  } else return res.status(400).json({ error: "Provide start or order[]" });
  await saveProject(proj);
  res.json({ ok: true, track });
});

app.post("/api/timeline/ripple", async (req, res) => {
  const { projectId, trackId = "v1" } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const track = findTrack(proj, trackId);
  if (!track) return res.status(404).json({ error: "Track not found" });
  rippleClose(track);
  await saveProject(proj);
  res.json({ ok: true, track });
});

app.delete("/api/timeline/clips/:clipId", async (req, res) => {
  const projectId = req.query.projectId || req.body?.projectId;
  const ripple = String(req.query.ripple || req.body?.ripple || "true") !== "false";
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  for (const track of proj.timeline.tracks) {
    const i = track.clips.findIndex((c) => c.id === req.params.clipId);
    if (i >= 0) {
      const removed = track.clips[i];
      track.clips.splice(i, 1);
      if (ripple) rippleDelete(track, removed.start, removed.duration);
      proj.timeline.transitions = (proj.timeline.transitions || []).filter((tr) => tr.fromClipId !== removed.id && tr.toClipId !== removed.id);
      await saveProject(proj);
      return res.json({ ok: true, ripple });
    }
  }
  res.status(404).json({ error: "Clip not found" });
});

app.post("/api/timeline/effects", async (req, res) => {
  const { projectId, clipId, effectId, params = {} } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const found = findClip(proj, clipId);
  if (!found) return res.status(404).json({ error: "Clip not found" });
  const plugins = await loadPlugins();
  const plugin = plugins.find((p) => p.id === effectId);
  if (!plugin) return res.status(404).json({ error: "unknown effect", available: plugins.map((p) => p.id) });
  found.clip.effects = found.clip.effects || [];
  found.clip.effects.push({ id: randomUUID(), effectId, params: { ...params }, appliedAt: new Date().toISOString() });
  await saveProject(proj);
  res.json({ ok: true, clip: found.clip });
});

app.post("/api/timeline/transitions", async (req, res) => {
  const { projectId, fromClipId, toClipId, transitionId = "transition.crossfade", duration = 1 } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  if (!findClip(proj, fromClipId) || !findClip(proj, toClipId)) return res.status(404).json({ error: "Clip(s) not found" });
  const tr = { id: randomUUID(), transitionId, fromClipId, toClipId, duration: Number(duration) || 1 };
  proj.timeline.transitions = (proj.timeline.transitions || []).filter((x) => !(x.fromClipId === fromClipId && x.toClipId === toClipId));
  proj.timeline.transitions.push(tr);
  await saveProject(proj);
  res.json({ ok: true, transition: tr });
});

app.get("/api/preview/frame", async (req, res) => {
  const projectId = req.query.projectId;
  const t = parseFloat(req.query.t || "0");
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const vTrack = findTrack(proj, "v1") || proj.timeline.tracks.find((x) => x.type === "video");
  const vClips = [...(vTrack?.clips || [])].sort((a, b) => a.start - b.start);
  if (!vClips.length) return res.status(400).json({ error: "No video clips" });
  const hit = resolveClipAtTime(vClips, t);
  if (!hit || !existsSync(hit.clip.sourcePath)) return res.status(400).json({ error: "No clip at time" });
  const out = join(PREVIEW_DIR, `${projectId}_${t.toFixed(2)}.jpg`);
  try {
    await execFileP("ffmpeg", ["-y", "-ss", String(Math.max(0, hit.sourceTime)), "-i", hit.clip.sourcePath, "-frames:v", "1", "-q:v", "3", out], { maxBuffer: 10e6 });
    res.type("image/jpeg").send(await fs.readFile(out));
  } catch (e) {
    res.status(500).json({ error: String(e.message || e) });
  }
});

app.get("/api/preview/info", async (req, res) => {
  const proj = await readProject(req.query.projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const vTrack = findTrack(proj, "v1");
  const clips = [...(vTrack?.clips || [])].sort((a, b) => a.start - b.start);
  res.json({ duration: trackEnd(vTrack || { clips: [] }), clipCount: clips.length, clips: clips.map((c) => ({ id: c.id, start: c.start, duration: c.duration, filename: c.filename })) });
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
    if (!clip.sourcePath || !existsSync(clip.sourcePath)) throw new Error(`Missing source ${clip.id}`);
    const seg = join(tmpDir, `seg_${String(i).padStart(3, "0")}.mp4`);
    const dur = clip.duration || clip.outPoint - clip.inPoint;
    const vf = [`scale=${width}:${height}:force_original_aspect_ratio=decrease`, `pad=${width}:${height}:(ow-iw)/2:(oh-ih)/2`, "fps=30", "format=yuv420p"];
    for (const ef of clip.effects || []) {
      if (ef.effectId === "effect.fade_in") vf.push(`fade=t=in:st=0:d=${ef.params?.duration ?? 1}`);
      else if (ef.effectId === "effect.fade_out") {
        const d = ef.params?.duration ?? 1;
        vf.push(`fade=t=out:st=${Math.max(0, dur - d)}:d=${d}`);
      } else if (ef.effectId === "effect.scale" && (ef.params?.zoom ?? 1) !== 1) vf.push(`scale=iw*${ef.params.zoom}:ih*${ef.params.zoom}`);
    }
    await execFileP("ffmpeg", ["-y", "-ss", String(clip.inPoint || 0), "-i", clip.sourcePath, "-t", String(dur), "-vf", vf.join(","), "-c:v", "libx264", "-an", seg], { maxBuffer: 20e6 });
    segmentPaths.push({ path: seg, clip, dur });
  }
  const transitions = proj.timeline.transitions || [];
  let silentVideo = join(tmpDir, "video_silent.mp4");
  const useXfade = segmentPaths.length >= 2 && transitions.some((tr) => tr.transitionId === "transition.crossfade");
  if (useXfade) {
    let current = segmentPaths[0].path, currentDur = segmentPaths[0].dur;
    for (let i = 1; i < segmentPaths.length; i++) {
      const prevClip = segmentPaths[i - 1].clip, nextClip = segmentPaths[i].clip;
      const tr = transitions.find((x) => x.fromClipId === prevClip.id && x.toClipId === nextClip.id);
      const fadeDur = Math.min(tr?.duration || 0, segmentPaths[i - 1].dur / 2, segmentPaths[i].dur / 2);
      const outSeg = join(tmpDir, `xf_${i}.mp4`);
      if (fadeDur > 0.05) {
        const offset = Math.max(0, currentDur - fadeDur);
        await execFileP("ffmpeg", ["-y", "-i", current, "-i", segmentPaths[i].path, "-filter_complex", `[0:v][1:v]xfade=transition=fade:duration=${fadeDur}:offset=${offset}[v]`, "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", outSeg], { maxBuffer: 30e6 });
        currentDur = currentDur + segmentPaths[i].dur - fadeDur; current = outSeg;
      } else {
        const list = join(tmpDir, `c_${i}.txt`);
        await fs.writeFile(list, `file '${current.replace(/'/g, "'\\''")}'\nfile '${segmentPaths[i].path.replace(/'/g, "'\\''")}'`);
        await execFileP("ffmpeg", ["-y", "-f", "concat", "-safe", "0", "-i", list, "-c:v", "libx264", "-pix_fmt", "yuv420p", outSeg], { maxBuffer: 20e6 });
        currentDur += segmentPaths[i].dur; current = outSeg;
      }
    }
    silentVideo = current;
  } else {
    const listFile = join(tmpDir, "list.txt");
    await fs.writeFile(listFile, segmentPaths.map((s) => `file '${s.path.replace(/'/g, "'\\''")}'`).join("\n"));
    await execFileP("ffmpeg", ["-y", "-f", "concat", "-safe", "0", "-i", listFile, "-c:v", "libx264", "-pix_fmt", "yuv420p", silentVideo], { maxBuffer: 20e6 });
  }
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
      for (const ef of clip.effects || []) if (ef.effectId === "effect.volume") args.push("-af", `volume=${ef.params?.level ?? 1}`);
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
  return { outputPath: outPath, segments: segmentPaths.length, xfade: useXfade };
}

app.post("/api/render", async (req, res) => {
  const { projectId, width, height, outputPath } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const jobId = randomUUID();
  db.renders.set(jobId, { status: "queued", projectId, jobId });
  setImmediate(async () => {
    try {
      db.renders.set(jobId, { status: "running", projectId, jobId });
      const result = await renderTimeline(proj, { jobId, width: width || 1280, height: height || 720, outputPath });
      db.renders.set(jobId, { status: "done", jobId, projectId, outputPath: result.outputPath, url: `/renders/${basename(result.outputPath)}`, segments: result.segments, xfade: result.xfade });
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

app.post("/api/agent/assemble", async (req, res) => {
  const { projectId, mediaIds = [], crossfade = 0, width = 1280, height = 720, fadeInFirst = false } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const track = findTrack(proj, "v1");
  if (!track) return res.status(404).json({ error: "Track v1 missing" });
  track.clips = []; proj.timeline.transitions = [];
  let t = 0; const added = [];
  for (const mediaId of mediaIds) {
    const mediaItem = (proj.media || []).find((m) => m.id === mediaId);
    if (!mediaItem) continue;
    const dur = mediaItem.duration || 5;
    const clip = { id: randomUUID(), mediaId, sourcePath: mediaItem.path, filename: mediaItem.filename, start: t, inPoint: 0, outPoint: dur, duration: dur, effects: [] };
    if (fadeInFirst && added.length === 0) clip.effects.push({ id: randomUUID(), effectId: "effect.fade_in", params: { duration: 1 } });
    track.clips.push(clip); added.push(clip); t += dur;
  }
  if (crossfade > 0 && added.length >= 2) {
    for (let i = 0; i < added.length - 1; i++) {
      proj.timeline.transitions.push({ id: randomUUID(), transitionId: "transition.crossfade", fromClipId: added[i].id, toClipId: added[i + 1].id, duration: Number(crossfade) });
    }
  }
  await saveProject(proj);
  const jobId = randomUUID();
  db.renders.set(jobId, { status: "queued", projectId, jobId });
  setImmediate(async () => {
    try {
      db.renders.set(jobId, { status: "running", projectId, jobId });
      const fresh = await readProject(projectId);
      const result = await renderTimeline(fresh, { jobId, width, height });
      db.renders.set(jobId, { status: "done", jobId, projectId, outputPath: result.outputPath, url: `/renders/${basename(result.outputPath)}`, segments: result.segments, xfade: result.xfade });
    } catch (e) {
      db.renders.set(jobId, { status: "error", jobId, projectId, error: String(e.message || e) });
    }
  });
  res.json({ ok: true, clips: added.map((c) => c.id), jobId, transitions: proj.timeline.transitions.length });
});

app.use(express.static(PUBLIC_DIR));
app.get("/", (_req, res) => res.sendFile(join(PUBLIC_DIR, "index.html")));
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Editor local en http://localhost:${PORT}`));
