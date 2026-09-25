/** Project CRUD */
export function registerProjects(app, ctx) {
  const {
    readProject, saveProject, emptyProject, db, PROJECTS_DIR, fs, join,
  } = ctx;

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
}
