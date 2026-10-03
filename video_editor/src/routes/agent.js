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
    const implemented = catalog.implemented || [];
    res.json({
      ...catalog,
      plugins: implemented.map((id) => ({ id })),
    });
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
    // MVP: proxy = misma media; proxyUrl para la UI (null si es path externo no servido)
    res.json({ ok: true, proxy: media, proxyUrl: media.url || null });
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
    // Render sync + job registrado para que el playbook pueda hacer poll GET /api/render/:jobId
    const { jobStore, db } = ctx;
    const jobId = randomUUID();
    const queued = { status: "queued", projectId, jobId, updatedAt: new Date().toISOString() };
    db.renders.set(jobId, queued);
    try { await jobStore.save(queued); } catch {}
    try {
      const running = { status: "running", projectId, jobId, updatedAt: new Date().toISOString() };
      db.renders.set(jobId, running);
      try { await jobStore.save(running); } catch {}
      const result = await renderTimelineSafe(proj, {
        width, height, useHwAccel, RENDER_DIR,
        jobId,
      });
      const done = {
        status: "done", projectId, jobId,
        outputPath: result.outputPath, url: result.url,
        segments: result.segments, percent: 100,
        updatedAt: new Date().toISOString(),
      };
      db.renders.set(jobId, done);
      try { await jobStore.save(done); } catch {}
      return res.json({
        ok: true, projectId, clips: used, render: true,
        jobId, poll: `/api/render/${jobId}`,
        ...result,
      });
    } catch (e) {
      const err = { status: "error", projectId, jobId, error: String(e.message || e).slice(0, 800), updatedAt: new Date().toISOString() };
      db.renders.set(jobId, err);
      try { await jobStore.save(err); } catch {}
      return res.status(500).json({ error: "Render falló", detail: String(e.message || e).slice(0, 800), jobId, poll: `/api/render/${jobId}` });
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
      editor_url: `http://127.0.0.1:3000/?projectId=${proj.id}`,
    });
  });

  // OTIO export (útil para agentes/Premiere)
  app.get("/api/projects/:id/otio", async (req, res) => {
    const proj = await readProject(req.params.id);
    if (!proj) return res.status(404).json({ error: "Project not found" });
    res.json(projectToOTIO(proj));
  });

  // OTIO import (la UI lo llama en btnOtioIn). Acepta OTIO Timeline.1 o {tracks}.
  app.post("/api/projects/:id/otio/import", async (req, res) => {
    const proj = await readProject(req.params.id);
    if (!proj) return res.status(404).json({ error: "Project not found" });
    const body = req.body || {};
    try {
      const stack = body.tracks?.children || body.timeline?.tracks?.children || [];
      if (!Array.isArray(stack) || !stack.length) {
        return res.status(400).json({ error: "OTIO sin tracks", hint: "Exporta con GET .../otio para ver el formato" });
      }
      const rateOf = (rt) => (rt && rt.rate) || 30;
      const toSec = (rt) => (rt ? (rt.value || 0) / rateOf(rt) : 0);
      const newTracks = [];
      for (const tr of stack) {
        const tid = String(tr.name || `v${newTracks.length + 1}`).slice(0, 16);
        const type = tr.kind === "Audio" ? "audio" : "video";
        const clips = [];
        let t = 0;
        for (const c of tr.children || []) {
          if (!c.source_range) continue;
          const dur = toSec(c.source_range.duration);
          const inP = toSec(c.source_range.start_time);
          const meta = c.metadata || {};
          const mediaRef = c.media_reference || {};
          clips.push({
            id: randomUUID().slice(0, 8),
            mediaId: mediaRef.metadata?.mediaId || null,
            filename: c.name || "clip",
            sourcePath: (mediaRef.target_url || "").replace(/^file:\/\//, "") || null,
            start: meta.gremlin_start_seconds ?? t,
            duration: dur || 5,
            inPoint: inP,
            outPoint: inP + (dur || 5),
            effects: mediaRef.metadata?.effects || [],
            keyframes: [],
          });
          t += dur || 5;
        }
        newTracks.push({ id: tid, type, clips });
      }
      if (!newTracks.length) return res.status(400).json({ error: "OTIO sin clips importables" });
      proj.timeline.tracks = newTracks;
      proj.timeline.transitions = body.metadata?.gremlin_transitions?.map((tr) => ({
        id: tr.gremlin_id || randomUUID().slice(0, 8),
        fromClipId: tr.metadata?.fromClipId,
        toClipId: tr.metadata?.toClipId,
        transitionId: tr.name || "transition.crossfade",
        duration: toSec(tr.out_offset) || 1,
      })) || [];
      await saveProject(proj);
      const total = newTracks.flatMap((t) => t.clips).length;
      return res.json({ ok: true, projectId: proj.id, tracks: newTracks.length, clips: total });
    } catch (e) {
      return res.status(400).json({ error: "OTIO inválido", detail: String(e.message || e).slice(0, 300) });
    }
  });
}
