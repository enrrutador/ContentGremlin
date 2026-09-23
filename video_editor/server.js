#!/usr/bin/env node
import express from "express";
import cors from "cors";
import multer from "multer";
import { randomUUID } from "crypto";
import { promises as fs } from "fs";
import { join } from "path";
import { execFile } from "child_process";
import { promisify } from "util";

const execFileP = promisify(execFile);
const app = express();
app.use(cors());
app.use(express.json({ limit: "10mb" }));

const WORK_DIR = process.cwd();
const MEDIA_DIR = join(WORK_DIR, "media");
const PROJECTS_DIR = join(WORK_DIR, "projects");
const PUBLIC_DIR = join(WORK_DIR, "public");

await Promise.all([
  fs.mkdir(MEDIA_DIR, { recursive: true }),
  fs.mkdir(PROJECTS_DIR, { recursive: true }),
  fs.mkdir(PUBLIC_DIR, { recursive: true })
]);

const upload = multer({ dest: MEDIA_DIR });

// Estado en memoria sencillo
const db = {
  projects: new Map(),
  renders: new Map()
};

// Helpers
async function readProject(id) {
  if (db.projects.has(id)) return db.projects.get(id);
  try {
    const data = await fs.readFile(join(PROJECTS_DIR, `${id}.json`), "utf-8");
    const proj = JSON.parse(data);
    db.projects.set(id, proj);
    return proj;
  } catch { return null; }
}
async function saveProject(proj) {
  db.projects.set(proj.id, proj);
  await fs.writeFile(join(PROJECTS_DIR, `${proj.id}.json`), JSON.stringify(proj, null, 2));
}

// API
app.post("/api/projects", async (req, res) => {
  const id = randomUUID();
  const project = {
    id,
    name: req.body?.name || "Untitled",
    media: [],
    timeline: {
      tracks: [
        { id: "v1", type: "video", clips: [] },
        { id: "a1", type: "audio", clips: [] }
      ]
    },
    createdAt: new Date().toISOString()
  };
  await saveProject(project);
  res.json({ id });
});

app.get("/api/projects/:id", async (req, res) => {
  const proj = await readProject(req.params.id);
  if (!proj) return res.status(404).json({ error: "Not found" });
  res.json(proj);
});

app.post("/api/media/import", upload.single("file"), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: "No file" });
  const id = randomUUID();
  const media = {
    id,
    filename: req.file.originalname,
    path: req.file.path,
    size: req.file.size
  };
  // responder con metadata
  res.json(media);
});

// Timeline clips
app.post("/api/timeline/clips", async (req, res) => {
  const { projectId, trackId, clip } = req.body;
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "Project not found" });
  const track = proj.timeline.tracks.find(t => t.id === trackId);
  if (!track) return res.status(404).json({ error: "Track not found" });
  const clipId = randomUUID();
  const newClip = { id: clipId, ...clip };
  track.clips.push(newClip);
  await saveProject(proj);
  res.json({ clipId });
});

app.post("/api/timeline/cut", async (req, res) => {
  res.json({ ok: true });
});

app.post("/api/timeline/effects", async (req, res) => {
  res.json({ ok: true });
});

app.post("/api/timeline/transitions", async (req, res) => {
  res.json({ ok: true });
});

app.post("/api/render", async (req, res) => {
  const { projectId, outputPath, width, height } = req.body;
  const jobId = randomUUID();
  db.renders.set(jobId, { status: "queued", projectId, outputPath });
  // simular render rápido con ffmpeg copy
  setImmediate(async () => {
    try {
      const proj = await readProject(projectId);
      const firstClip = proj?.timeline.tracks?.[0]?.clips?.[0];
      if (!firstClip) throw new Error("No clips");
      // demo: copy first media
      const input = firstClip.sourcePath || join(MEDIA_DIR, "placeholder.mp4");
      const out = outputPath || join(MEDIA_DIR, `${jobId}.mp4`);
      // simplificado
      await execFileP("ffmpeg", ["-y", "-i", input, "-vf", `scale=${width||1280}:${height||720}`, out]);
      db.renders.set(jobId, { status: "done", jobId, outputPath: out });
    } catch (e) {
      db.renders.set(jobId, { status: "error", error: String(e) });
    }
  });
  res.json({ jobId });
});

app.get("/api/render/:jobId", (req, res) => {
  const job = db.renders.get(req.params.jobId);
  if (!job) return res.status(404).json({ error: "Job not found" });
  res.json(job);
});

// Frontend básico
app.use(express.static(PUBLIC_DIR));
app.get("/", (req, res) => {
  res.sendFile(join(PUBLIC_DIR, "index.html"));
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Editor local en http://localhost:${PORT}`);
});
