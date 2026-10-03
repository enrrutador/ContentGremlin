/** Preview: info + frame + montage */
import { join } from "path";

export function registerPreview(app, ctx) {
  const { readProject, probeMedia, execFileP } = ctx;

  app.get("/api/preview/info", async (req, res) => {
    const proj = await readProject(req.query.projectId);
    if (!proj) return res.status(404).json({ error: "Project not found" });
    const tracks = proj.timeline?.tracks || [];
    const clips = tracks.flatMap((t) => (t.clips || []).map((c) => ({ ...c, trackId: t.id })));
    const duration = clips.reduce((m, c) => Math.max(m, (c.start || 0) + (c.duration || 0)), 0);
    res.json({
      projectId: proj.id,
      name: proj.name,
      duration,
      tracks: tracks.map((t) => ({ id: t.id, type: t.type, clips: t.clips?.length || 0 })),
      clips: clips.length,
      media: (proj.media || []).length,
      transitions: (proj.timeline?.transitions || []).length,
    });
  });

  // Frame JPEG en t segundos (del primer source válido)
  app.get("/api/preview/frame", async (req, res) => {
    const t = Number(req.query.t ?? 1);
    const proj = await readProject(req.query.projectId);
    if (!proj) return res.status(404).json({ error: "Project not found" });
    const src =
      (proj.media || []).map((m) => m.path).find(Boolean) ||
      (proj.timeline?.tracks || []).flatMap((tr) => tr.clips || []).map((c) => c.sourcePath).find(Boolean);
    if (!src) return res.status(404).json({ error: "Sin media para preview" });
    try {
      const { stdout } = await execFileP(
        "ffmpeg",
        ["-y", "-ss", String(Math.max(0, t)), "-i", src, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "mjpeg", "pipe:1"],
        { maxBuffer: 15e6, encoding: "buffer" }
      );
      res.setHeader("Content-Type", "image/jpeg");
      res.send(stdout);
    } catch (e) {
      res.status(500).json({ error: "FFmpeg frame falló", detail: String(e.message || e).slice(0, 500) });
    }
  });

  app.post("/api/preview/montage", async (req, res) => {
    const { projectId } = req.body || {};
    const proj = await readProject(projectId);
    if (!proj) return res.status(404).json({ error: "Project not found" });
    const clips = (proj.timeline?.tracks || []).flatMap((t) => t.clips || []);
    const duration = clips.reduce((m, c) => Math.max(m, (c.start || 0) + (c.duration || 0)), 0);
    // Probe rápido del primer source para dimensiones
    let probe = null;
    const first = (proj.media || [])[0];
    if (first?.path) {
      try { probe = await probeMedia(first.path); } catch {}
    }
    res.json({
      projectId: proj.id,
      duration,
      clips: clips.length,
      probe,
      hint: "Usa GET /api/preview/frame?projectId=&t= para thumbnail",
    });
  });
}
