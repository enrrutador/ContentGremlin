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
    const { projectId, width = 640, height = 360 } = req.body || {};
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
    // Render preview real para que la UI pueda mostrarlo (j.url)
    try {
      const { renderTimelineSafe } = ctx;
      const { join, basename } = ctx;
      const { PREVIEW_DIR } = ctx;
      const { promises: fsp } = await import("fs");
      await fsp.mkdir(PREVIEW_DIR, { recursive: true });
      const outName = `montage_${proj.id.slice(0, 8)}.mp4`;
      const result = await renderTimelineSafe(proj, {
        width: Number(width) || 640,
        height: Number(height) || 360,
        outputPath: join(PREVIEW_DIR, outName),
        RENDER_DIR: PREVIEW_DIR,
      });
      const url = `/renders/preview/${basename(result.outputPath)}`;
      return res.json({
        projectId: proj.id,
        duration,
        clips: clips.length,
        probe,
        url,
        outputPath: result.outputPath,
        hint: "Preview listo",
      });
    } catch (e) {
      // Fallback: al menos frame URL si el render falla
      return res.json({
        projectId: proj.id,
        duration,
        clips: clips.length,
        probe,
        url: `/api/preview/frame?projectId=${proj.id}&t=1`,
        error: String(e.message || e).slice(0, 300),
        hint: "Render preview falló, usa frame",
      });
    }
  });
}
