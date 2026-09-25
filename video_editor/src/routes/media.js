/** Media import */
export function registerMedia(app, ctx) {
  const {
    readProject, saveProject, probeMedia, upload, randomUUID, basename,
  } = ctx;

  app.post("/api/media/import", upload.single("file"), async (req, res) => {
    if (!req.file) return res.status(400).json({ error: "No file" });
    const projectId = req.body?.projectId || req.query?.projectId;
    const meta = await probeMedia(req.file.path);
    const media = {
      id: randomUUID(),
      filename: req.file.originalname,
      storedName: basename(req.file.path),
      path: req.file.path,
      url: `/media/${basename(req.file.path)}`,
      size: req.file.size,
      duration: meta.duration,
      width: meta.width,
      height: meta.height,
      hasVideo: meta.hasVideo,
      hasAudio: meta.hasAudio,
      codec: meta.codec,
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
}
