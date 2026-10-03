/** Agent: assemble, status, effects, capabilities + integrate/gremlin + import-paths */
import { promises as fs } from "fs";
import { basename } from "path";
import { randomUUID } from "crypto";

export function registerAgent(app, ctx) {
  const {
    readProject, saveProject, emptyProject, trackEnd, findTrack,
    probeMedia, renderTimelineSafe, projectToOTIO,
    MEDIA_DIR, PROJECTS_DIR, PUBLIC_DIR, RENDER_DIR, PLUGINS_DIR, join, existsSync,
  } = ctx;

  async function loadCatalog() {
    try {
      const raw = await fs.readFile(join(PLUGINS_DIR, "catalog.json"), "utf-8");
      return JSON.parse(raw);
    } catch {
      return { version: "4.0", implemented: [] };
    }
  }

  app.get("/api/capabilities", async (_req, res) => {
    const catalog = await loadCatalog();
    res.json({
      name: "contentgremlin-editor",
      routes: ["projects", "media", "timeline", "preview", "render", "agent"],
      effects: catalog.implemented || [],
      ffmpeg: true,
    });
  });

  app.get("/api/plugins", async (_req, res) => {
    const catalog = await loadCatalog();
    res.json(catalog);
  });

  app.get("/api/agent/effects", async (_req, res) => {
    const catalog = await loadCatalog();
    res.json({ effects: catalog.implemented || [], catalog });
  });

  app.get("/api/agent/status", async (req, res) => {
    const proj = await readProject(req.query.projectId);
    if (!proj) return res.status(404).json({ error: "Project not found" });
    const clips = (proj.timeline?.tracks || []).flatMap((t) => t.clips || []);
    const duration = clips.reduce((m, c) => Math.max(m, (c.start || 0) + (c.duration || 0)), 0);
    const missing = (proj.media || []).filter((m) => !existsSync(m.path)).map((m) => m.id);
    res.json({
      projectId: proj.id,
      name: proj.name,
      media: (proj.media || []).length,
      clips: clips.length,
      duration,
      transitions: (proj.timeline?.transitions || []).length,
      missing,
      tips: missing.length ? ["Re-importa media faltante"] : [],
    });
  });

  // Importar desde rutas absolutas (agente/Gremlin)
  app.post("/api/media/import-paths", async (req, res) => {
    const { projectId, paths } = req.body || {};
    if (!projectId || !Array.isArray(paths) || !paths.length) {
      return res.status(400).json({ error: "projectId y paths[] requeridos" });
    }
    const proj = await readProject(projectId);
    if (!proj) return res.status(404).json({ error: "Project not found" });
    const added = [];
    for (const p of paths) {
      try {
        await fs.access(p);
      } catch {
        added.push({ path: p, error: "No existe en disco del editor" });
        continue;
      }
      const meta = await probeMedia(p).catch(() => ({}));
      const media = {
        id: randomUUID().slice(0, 8),
        filename: basename(p),
        storedName: basename(p),
        path: p,
        url: null,
        size: null,
        duration: meta.duration || 0,
        width: meta.width || null,
        height: meta.height || null,
        hasVideo: meta.hasVideo ?? true,
        hasAudio: meta.hasAudio ?? false,
        codec: meta.codec || null,
        importedAt: new Date().toISOString(),
      };
      proj.media.push(media);
      added.push(media);
    }
    await saveProject(proj);
    res.json({ media: added, projectId });
  });

  app.post("/api/media/proxy", async (req, res) => {
    const { projectId, mediaId } = req.body || {};
    const proj = await readProject(projectId);
    if (!proj) return res.status(404).json({ error: "Project not found" });
    const media = (proj.media || []).find((m) => m.id === mediaId);
    if (!media) return res.status(404).json({ error: "Media no encontrada" });
    // MVP: devuelve la misma media como proxy
    res.json({ ok: true, proxy: media });
  });

  // Ensamblado rápido: mediaIds en orden → clips en v1 + render opcional
  app.post("/api/agent/assemble", async (req, res) => {
    const {
      projectId, mediaIds = [], crossfade = 0, fadeInFirst = false,
      width = 1280, height = 720, render = true, useHwAccel = false,
    } = req.body || {};
    if (!projectId) return res.status(400).json({ error: "projectId requerido" });
    const proj = await readProject(projectId);
    if (!proj) return res.status(404).json({ error: "Project not found" });
    const track = findTrack(proj, "v1") || proj.timeline.tracks[0];
    // Limpia v1 para re-ensamblar determinístico
    track.clips = [];
    let t = 0;
    const used = [];
    for (const mid of mediaIds) {
      const media = (proj.media || []).find((m) => m.id === mid);
      if (!media) continue;
      const duration = Number(media.duration) > 0 ? Number(media.duration) : 5;
      const clip = {
        id: randomUUID().slice(0, 8),
        mediaId: media.id,
        filename: media.filename,
        sourcePath: media.path,
        start: t,
        duration,
        inPoint: 0,
        outPoint: duration,
        effects: fadeInFirst && used.length === 0 ? [{ id: "effect.fade_in", params: { duration: 1 } }] : [],
        keyframes: [],
      };
      track.clips.push(clip);
      used.push(clip.id);
      t += duration - (crossfade > 0 && used.length > 1 ? Number(crossfade) : 0);
    }
    // Crossfades como transiciones
    if (crossfade > 0) {
      proj.timeline.transitions = proj.timeline.transitions || [];
      for (let i = 0; i < used.length - 1; i++) {
        proj.timeline.transitions.push({
          id: randomUUID().slice(0, 8),
          fromClipId: used[i], toClipId: used[i + 1],
          transitionId: "transition.crossfade",
          duration: Number(crossfade),
        });
      }
    }
    await saveProject(proj);
    if (!render) return res.json({ ok: true, projectId, clips: used, render: false });
    try {
      const result = await renderTimelineSafe(proj, {
        width, height, useHwAccel, RENDER_DIR,
        jobId: randomUUID().slice(0, 8),
      });
      return res.json({ ok: true, projectId, clips: used, render: true, ...result });
    } catch (e) {
      return res.status(500).json({ error: "Render falló", detail: String(e.message || e).slice(0, 800) });
    }
  });

  // Bridge Gremlin → Editor
  app.post("/api/integrate/gremlin", async (req, res) => {
    const { name = "Desde Gremlin", videoPath = null, mediaPaths = [], autoAssemble = true, crossfade = 0 } = req.body || {};
    const paths = [...(mediaPaths || [])];
    if (videoPath && !paths.includes(videoPath)) paths.unshift(videoPath);
    const proj = emptyProject(name);
    // Importa paths existentes
    for (const p of paths) {
      try {
        await fs.access(p);
        const meta = await probeMedia(p).catch(() => ({}));
        proj.media.push({
          id: randomUUID().slice(0, 8),
          filename: basename(p),
          storedName: basename(p),
          path: p,
          url: null,
          duration: meta.duration || 0,
          width: meta.width || null,
          height: meta.height || null,
          hasVideo: meta.hasVideo ?? true,
          hasAudio: meta.hasAudio ?? false,
          codec: meta.codec || null,
          importedAt: new Date().toISOString(),
        });
      } catch {}
    }
    if (autoAssemble) {
      const track = proj.timeline.tracks[0];
      let t = 0;
      for (const m of proj.media) {
        const duration = Number(m.duration) > 0 ? Number(m.duration) : 5;
        track.clips.push({
          id: randomUUID().slice(0, 8),
          mediaId: m.id,
          filename: m.filename,
          sourcePath: m.path,
          start: t, duration, inPoint: 0, outPoint: duration,
          effects: [], keyframes: [],
        });
        t += duration - (crossfade > 0 ? Number(crossfade) : 0);
      }
    }
    await saveProject(proj);
    res.json({
      ok: true,
      projectId: proj.id,
      name: proj.name,
      media: proj.media.length,
      clips: proj.timeline.tracks[0]?.clips?.length || 0,
      editor_url: `http://127.0.0.1:3000/?project=${proj.id}`,
    });
  });

  // OTIO export (útil para agentes/Premiere)
  app.get("/api/projects/:id/otio", async (req, res) => {
    const proj = await readProject(req.params.id);
    if (!proj) return res.status(404).json({ error: "Project not found" });
    res.json(projectToOTIO(proj));
  });
}
