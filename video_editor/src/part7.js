  db.renders.set(jobId, { status: "queued", projectId, jobId });
  setImmediate(async () => {
    try {
      const run = { status: "running", projectId, jobId, updatedAt: new Date().toISOString() }; db.renders.set(jobId, run); await jobStore.save(run);
      const fresh = await readProject(projectId);
      const result = await renderTimeline(fresh, { jobId, width, height });
      const done = { status: "done", jobId, projectId, outputPath: result.outputPath, url: `/renders/${basename(result.outputPath)}`, segments: result.segments, xfade: result.xfade, updatedAt: new Date().toISOString() };
      db.renders.set(jobId, done); await jobStore.save(done);
    } catch (e) {
      const err = { status: "error", jobId, projectId, error: String(e.message || e), updatedAt: new Date().toISOString() };
      db.renders.set(jobId, err); await jobStore.save(err);
    }
  });
  res.json({ ok: true, clips: added.map((c) => c.id), jobId, transitions: proj.timeline.transitions.length });
});

app.post("/api/projects/:id/otio/import", async (req, res) => {
  const proj = await readProject(req.params.id);
  if (!proj) return res.status(404).json({ error: "no project" });
  const otio = req.body;
  if (!otio || !otio.tracks) return res.status(400).json({ error: "invalid OTIO JSON" });
  const stack = otio.tracks?.children || otio.tracks || [];
  const rate = otio.global_start_time?.rate || 30;
  proj.timeline.tracks = proj.timeline.tracks || [];
  // clear video track clips
  const vTrack = findTrack(proj, "v1") || proj.timeline.tracks.find((t) => t.type === "video");
  if (vTrack) vTrack.clips = [];
  for (const track of (Array.isArray(stack) ? stack : [])) {
    const kind = (track.kind || "").toLowerCase();
    const target = kind === "audio" ? findTrack(proj, "a1") : vTrack;
    if (!target) continue;
    let t = 0;
    for (const child of track.children || []) {
      if ((child.OTIO_SCHEMA || "").startsWith("Clip")) {
        const durFrames = child.source_range?.duration?.value || 0;
        const inFrames = child.source_range?.start_time?.value || 0;
        const r = child.source_range?.duration?.rate || rate;
        const duration = r ? durFrames / r : 0;
        const inPoint = r ? inFrames / r : 0;
        const url = child.media_reference?.target_url || "";
        const path = url.replace(/^file:\/\//, "");
        const clip = {
          id: randomUUID(),
          mediaId: child.media_reference?.metadata?.mediaId || null,
          sourcePath: path || null,
          filename: child.name || basename(path || "clip"),
          start: t,
          inPoint,
          outPoint: inPoint + duration,
          duration,
          effects: child.media_reference?.metadata?.effects || [],
        };
        target.clips.push(clip);
        t += duration;
      }
    }
  }
  await saveProject(proj);
  res.json({ ok: true, project: proj });
});

/** Quick low-res montage preview (max 30s, 640w) */
app.post("/api/preview/montage", async (req, res) => {
  const { projectId, maxDuration = 30 } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const jobId = "preview_" + randomUUID().slice(0, 8);
  try {
    const result = await renderTimeline(proj, {
      jobId,
      width: 640,
      height: 360,
      outputPath: join(RENDER_DIR, `${jobId}.mp4`),
    });
    res.json({ ok: true, url: `/renders/${basename(result.outputPath)}`, jobId });
  } catch (e) {
    res.status(500).json({ error: String(e.message || e) });
  }
});

app.use(express.static(PUBLIC_DIR));
app.get("/", (_req, res) => res.sendFile(join(PUBLIC_DIR, "index.html")));
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Editor local en http://localhost:${PORT}`));
