/** Timeline: clips, cut, trim, move, ripple, effects, transitions, keyframes */
import { randomUUID } from "crypto";

export function registerTimeline(app, ctx) {
  const {
    readProject, saveProject, findTrack, findClip, trackEnd,
    rippleClose, rippleDelete,
  } = ctx;

  async function needProject(projectId, res) {
    const proj = await readProject(projectId);
    if (!proj) {
      res.status(404).json({ error: "Project not found", hint: "POST /api/projects primero" });
      return null;
    }
    return proj;
  }

  // Agregar clip desde media
  app.post("/api/timeline/clips", async (req, res) => {
    const { projectId, trackId = "v1", mediaId, start } = req.body || {};
    if (!projectId || !mediaId) {
      return res.status(400).json({ error: "projectId y mediaId son requeridos" });
    }
    const proj = await needProject(projectId, res);
    if (!proj) return;
    const track = findTrack(proj, trackId) || proj.timeline.tracks[0];
    if (!track) return res.status(400).json({ error: "Track no encontrado", available: proj.timeline.tracks.map((t) => t.id) });
    const media = (proj.media || []).find((m) => m.id === mediaId);
    if (!media) return res.status(404).json({ error: "Media no encontrada en proyecto", hint: "GET /api/projects/:id/media" });
    const duration = Number(media.duration) > 0 ? Number(media.duration) : 5;
    const clip = {
      id: randomUUID().slice(0, 8),
      mediaId: media.id,
      filename: media.filename,
      sourcePath: media.path,
      start: start != null ? Number(start) : trackEnd(track),
      duration,
      inPoint: 0,
      outPoint: duration,
      effects: [],
      keyframes: [],
    };
    track.clips.push(clip);
    track.clips.sort((a, b) => a.start - b.start);
    await saveProject(proj);
    res.json({ clip, trackId: track.id });
  });

  // Cortar un clip en dos
  app.post("/api/timeline/cut", async (req, res) => {
    const { projectId, clipId, atRelative } = req.body || {};
    if (!projectId || !clipId || atRelative == null) {
      return res.status(400).json({ error: "projectId, clipId y atRelative requeridos" });
    }
    const proj = await needProject(projectId, res);
    if (!proj) return;
    const found = findClip(proj, clipId);
    if (!found) return res.status(404).json({ error: "Clip no encontrado" });
    const { track, clip } = found;
    const at = Number(atRelative);
    if (!(at > 0 && at < clip.duration)) {
      return res.status(400).json({ error: "atRelative fuera de rango", duration: clip.duration });
    }
    const second = {
      ...structuredClone(clip),
      id: randomUUID().slice(0, 8),
      start: clip.start + at,
      duration: clip.duration - at,
      inPoint: (clip.inPoint || 0) + at,
    };
    clip.duration = at;
    clip.outPoint = (clip.inPoint || 0) + at;
    track.clips.push(second);
    track.clips.sort((a, b) => a.start - b.start);
    await saveProject(proj);
    res.json({ first: clip, second });
  });

  // Trim in/out
  app.post("/api/timeline/trim", async (req, res) => {
    const { projectId, clipId, inPoint, outPoint } = req.body || {};
    if (!projectId || !clipId) return res.status(400).json({ error: "projectId y clipId requeridos" });
    const proj = await needProject(projectId, res);
    if (!proj) return;
    const found = findClip(proj, clipId);
    if (!found) return res.status(404).json({ error: "Clip no encontrado" });
    const { clip } = found;
    if (inPoint != null) {
      const delta = Number(inPoint) - (clip.inPoint || 0);
      clip.inPoint = Number(inPoint);
      clip.start = (clip.start || 0) + delta;
      clip.duration = Math.max(0.1, clip.duration - delta);
    }
    if (outPoint != null) {
      clip.outPoint = Number(outPoint);
      clip.duration = Math.max(0.1, Number(outPoint) - (clip.inPoint || 0));
    }
    await saveProject(proj);
    res.json({ clip });
  });

  // Mover / reordenar
  app.post("/api/timeline/move", async (req, res) => {
    const { projectId, clipId, start, trackId, order } = req.body || {};
    if (!projectId) return res.status(400).json({ error: "projectId requerido" });
    const proj = await needProject(projectId, res);
    if (!proj) return;
    // Reorden total por lista de ids (dentro de su track)
    if (Array.isArray(order)) {
      let moved = 0;
      for (const track of proj.timeline.tracks) {
        const ids = new Set(order);
        const inTrack = track.clips.filter((c) => ids.has(c.id));
        if (inTrack.length) {
          const byId = new Map(inTrack.map((c) => [c.id, c]));
          const sorted = order.map((id) => byId.get(id)).filter(Boolean);
          const others = track.clips.filter((c) => !ids.has(c.id));
          // Reasigna starts en orden
          let t = 0;
          for (const c of [...sorted, ...others]) { c.start = t; t += c.duration || 0; }
          track.clips = [...sorted, ...others];
          moved += sorted.length;
        }
      }
      await saveProject(proj);
      return res.json({ ok: true, moved });
    }
    if (!clipId) return res.status(400).json({ error: "clipId u order requeridos" });
    const found = findClip(proj, clipId);
    if (!found) return res.status(404).json({ error: "Clip no encontrado" });
    let { track, clip } = found;
    if (trackId && trackId !== track.id) {
      const dest = findTrack(proj, trackId);
      if (!dest) return res.status(404).json({ error: "Track destino no encontrado" });
      track.clips = track.clips.filter((c) => c.id !== clip.id);
      dest.clips.push(clip);
      track = dest;
    }
    if (start != null) clip.start = Number(start);
    track.clips.sort((a, b) => a.start - b.start);
    await saveProject(proj);
    res.json({ clip, trackId: track.id });
  });

  // Cerrar huecos
  app.post("/api/timeline/ripple", async (req, res) => {
    const { projectId, trackId } = req.body || {};
    if (!projectId) return res.status(400).json({ error: "projectId requerido" });
    const proj = await needProject(projectId, res);
    if (!proj) return;
    const targets = trackId ? [findTrack(proj, trackId)].filter(Boolean) : proj.timeline.tracks;
    for (const t of targets) rippleClose(t);
    await saveProject(proj);
    res.json({ ok: true, tracks: targets.map((t) => t.id) });
  });

  // Borrar clip
  app.delete("/api/timeline/clips/:id", async (req, res) => {
    const projectId = req.query.projectId || req.body?.projectId;
    const ripple = String(req.query.ripple ?? "true") !== "false";
    if (!projectId) return res.status(400).json({ error: "projectId requerido (?projectId=)" });
    const proj = await needProject(projectId, res);
    if (!proj) return;
    const found = findClip(proj, req.params.id);
    if (!found) return res.status(404).json({ error: "Clip no encontrado" });
    const { track, clip } = found;
    track.clips = track.clips.filter((c) => c.id !== clip.id);
    if (ripple) rippleDelete(track, clip.start, clip.duration);
    await saveProject(proj);
    res.json({ ok: true, removed: clip.id });
  });

  // Efectos
  app.post("/api/timeline/effects", async (req, res) => {
    const { projectId, clipId, effectId, params = {} } = req.body || {};
    if (!projectId || !clipId || !effectId) {
      return res.status(400).json({ error: "projectId, clipId y effectId requeridos" });
    }
    const proj = await needProject(projectId, res);
    if (!proj) return;
    const found = findClip(proj, clipId);
    if (!found) return res.status(404).json({ error: "Clip no encontrado" });
    found.clip.effects = found.clip.effects || [];
    found.clip.effects.push({ id: effectId, params, at: new Date().toISOString() });
    await saveProject(proj);
    res.json({ ok: true, clip: found.clip });
  });

  // Transiciones
  app.post("/api/timeline/transitions", async (req, res) => {
    const { projectId, fromClipId, toClipId, transitionId = "transition.crossfade", duration = 1 } = req.body || {};
    if (!projectId || !fromClipId || !toClipId) {
      return res.status(400).json({ error: "projectId, fromClipId y toClipId requeridos" });
    }
    const proj = await needProject(projectId, res);
    if (!proj) return;
    proj.timeline.transitions = proj.timeline.transitions || [];
    const tr = {
      id: randomUUID().slice(0, 8),
      fromClipId, toClipId, transitionId,
      duration: Number(duration) || 1,
    };
    proj.timeline.transitions.push(tr);
    await saveProject(proj);
    res.json({ ok: true, transition: tr });
  });

  // Keyframes opacidad
  app.post("/api/timeline/keyframes", async (req, res) => {
    const { projectId, clipId, keyframes } = req.body || {};
    if (!projectId || !clipId || !Array.isArray(keyframes)) {
      return res.status(400).json({ error: "projectId, clipId y keyframes[] requeridos" });
    }
    const proj = await needProject(projectId, res);
    if (!proj) return;
    const found = findClip(proj, clipId);
    if (!found) return res.status(404).json({ error: "Clip no encontrado" });
    found.clip.keyframes = keyframes;
    await saveProject(proj);
    res.json({ ok: true, clip: found.clip });
  });
}
