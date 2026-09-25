/** Render jobs */
export function registerRender(app, ctx) {
  const {
    readProject, renderTimelineSafe, jobStore, db, randomUUID, basename, RENDER_DIR,
  } = ctx;

  app.post("/api/render", async (req, res) => {
    const { projectId, width, height, outputPath } = req.body || {};
    const proj = await readProject(projectId);
    if (!proj) return res.status(404).json({ error: "Project not found" });
    const jobId = randomUUID();
    const q = { status: "queued", projectId, jobId, updatedAt: new Date().toISOString() };
    db.renders.set(jobId, q);
    await jobStore.save(q);
    setImmediate(async () => {
      try {
        const run = { status: "running", projectId, jobId, updatedAt: new Date().toISOString() };
        db.renders.set(jobId, run);
        await jobStore.save(run);
        const result = await renderTimelineSafe(proj, {
          jobId,
          width: width || 1280,
          height: height || 720,
          outputPath,
          useHwAccel: !!(req.body && req.body.useHwAccel),
          RENDER_DIR,
          onProgress: async (p) => {
            const cur = {
              status: "running",
              jobId,
              projectId,
              percent: p.percent || 0,
              phase: p.phase,
              updatedAt: new Date().toISOString(),
            };
            db.renders.set(jobId, cur);
            await jobStore.save(cur);
          },
        });
        const done = {
          status: "done",
          jobId,
          projectId,
          outputPath: result.outputPath,
          url: `/renders/${basename(result.outputPath)}`,
          segments: result.segments,
          xfade: result.xfade,
          percent: 100,
          updatedAt: new Date().toISOString(),
        };
        db.renders.set(jobId, done);
        await jobStore.save(done);
      } catch (e) {
        const err = {
          status: "error",
          jobId,
          projectId,
          error: String(e.message || e),
          updatedAt: new Date().toISOString(),
        };
        db.renders.set(jobId, err);
        await jobStore.save(err);
      }
    });
    res.json({ jobId });
  });

  app.get("/api/render/:jobId", async (req, res) => {
    let job = db.renders.get(req.params.jobId) || (await jobStore.get(req.params.jobId));
    if (!job) return res.status(404).json({ error: "Job not found" });
    res.json(job);
  });

  app.get("/api/render", async (_req, res) => {
    const jobs = await jobStore.list(50);
    res.json({ jobs });
  });
}
