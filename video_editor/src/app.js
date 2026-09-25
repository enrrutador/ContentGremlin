#!/usr/bin/env node
/** ContentGremlin Editor — modular app */
import express from "express";
import cors from "cors";
import multer from "multer";
import { randomUUID } from "crypto";
import { promises as fs } from "fs";
import { existsSync } from "fs";
import { join, extname, basename } from "path";
import { fileURLToPath } from "url";
import { dirname } from "path";
import { projectToOTIO } from "../lib/otio.js";
import { createJobStore } from "../lib/jobs.js";
import {
  db, emptyProject, readProject, saveProject,
  findTrack, findClip, trackEnd, rippleClose, rippleDelete, resolveClipAtTime,
} from "./lib/project.js";
import { execFileP, videoEncoderArgs, probeMedia, loadPlugins } from "./lib/media.js";
import { renderTimelineSafe } from "./lib/render.js";
import { registerProjects } from "./routes/projects.js";
import { registerMedia } from "./routes/media.js";
import { registerTimeline } from "./routes/timeline.js";
import { registerPreview } from "./routes/preview.js";
import { registerRender } from "./routes/render.js";
import { registerAgent } from "./routes/agent.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const MEDIA_DIR = join(ROOT, "media");
const PROJECTS_DIR = join(ROOT, "projects");
const PUBLIC_DIR = join(ROOT, "public");
const PLUGINS_DIR = join(ROOT, "plugins");
const RENDER_DIR = join(ROOT, "renders");
const PREVIEW_DIR = join(RENDER_DIR, "preview");
const JOBS_DIR = join(ROOT, "jobs");
const PORT = Number(process.env.PORT) || 3000;

const jobStore = createJobStore(JOBS_DIR);
await Promise.all(
  [MEDIA_DIR, PROJECTS_DIR, PUBLIC_DIR, RENDER_DIR, PREVIEW_DIR, JOBS_DIR].map((d) =>
    fs.mkdir(d, { recursive: true })
  )
);

const app = express();
app.use(cors());
app.use(express.json({ limit: "20mb" }));
app.use("/media", express.static(MEDIA_DIR));
app.use("/renders", express.static(RENDER_DIR));

const upload = multer({
  storage: multer.diskStorage({
    destination: (_r, _f, cb) => cb(null, MEDIA_DIR),
    filename: (_r, file, cb) =>
      cb(null, `${randomUUID().slice(0, 8)}${extname(file.originalname) || ".bin"}`),
  }),
  limits: { fileSize: 2 * 1024 * 1024 * 1024 },
});

const ctx = {
  readProject, saveProject, emptyProject, findTrack, findClip, trackEnd,
  rippleClose, rippleDelete, resolveClipAtTime, probeMedia, loadPlugins,
  renderTimelineSafe, projectToOTIO, jobStore, db, upload, randomUUID,
  MEDIA_DIR, PROJECTS_DIR, RENDER_DIR, PREVIEW_DIR, PUBLIC_DIR, PLUGINS_DIR,
  fs, join, basename, existsSync, execFileP, videoEncoderArgs,
};

registerProjects(app, ctx);
registerMedia(app, ctx);
registerTimeline(app, ctx);
registerPreview(app, ctx);
registerRender(app, ctx);
registerAgent(app, ctx);

app.use(express.static(PUBLIC_DIR));
app.get("/", (_req, res) => res.sendFile(join(PUBLIC_DIR, "index.html")));

app.listen(PORT, () => {
  console.log(`Editor modular en http://localhost:${PORT}`);
  console.log(`  routes: projects, media, timeline, preview, render, agent`);
});
