  }
  const sourceCut = clip.inPoint + (cutAt - clip.start);
  const left = { ...clip, outPoint: sourceCut, duration: sourceCut - clip.inPoint };
  const right = { ...clip, id: randomUUID(), start: cutAt, inPoint: sourceCut, outPoint: clip.outPoint, duration: clip.outPoint - sourceCut, effects: [...(clip.effects || [])] };
  const idx = track.clips.findIndex((c) => c.id === clipId);
  track.clips.splice(idx, 1, left, right);
  await saveProject(proj);
  res.json({ ok: true, left, right });
});
app.post("/api/timeline/trim", async (req, res) => {
  const { projectId, clipId, inPoint, outPoint, start, duration } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const found = findClip(proj, clipId);
  if (!found) return res.status(404).json({ error: "Clip not found" });
  const { clip } = found;
  if (inPoint != null) clip.inPoint = Math.max(0, Number(inPoint));
  if (outPoint != null) clip.outPoint = Number(outPoint);
  if (start != null) clip.start = Number(start);
  if (duration != null) { clip.duration = Number(duration); clip.outPoint = clip.inPoint + clip.duration; }
  else clip.duration = clip.outPoint - clip.inPoint;
  if (clip.duration <= 0) return res.status(400).json({ error: "Invalid trim" });
  await saveProject(proj);
  res.json({ ok: true, clip });
});
app.post("/api/timeline/move", async (req, res) => {
  const { projectId, clipId, start, order, pack = false } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const found = findClip(proj, clipId);
  if (!found) return res.status(404).json({ error: "Clip not found" });
  const { track, clip } = found;
  if (Array.isArray(order)) {
    const map = new Map(track.clips.map((c) => [c.id, c]));
    const next = []; let t = 0;
    for (const id of order) {
      const c = map.get(id); if (!c) continue;
      c.start = t; t += c.duration || 0; next.push(c); map.delete(id);
    }
    for (const c of map.values()) { c.start = t; t += c.duration || 0; next.push(c); }
    track.clips = next;
  } else if (start != null) {
    clip.start = Math.max(0, Number(start));
    track.clips.sort((a, b) => a.start - b.start);
    if (pack) rippleClose(track);
  } else return res.status(400).json({ error: "Provide start or order[]" });
  await saveProject(proj);
  res.json({ ok: true, track });
});
app.post("/api/timeline/ripple", async (req, res) => {
  const { projectId, trackId = "v1" } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const track = findTrack(proj, trackId);
  if (!track) return res.status(404).json({ error: "Track not found" });
  rippleClose(track);
  await saveProject(proj);
  res.json({ ok: true, track });
});
app.delete("/api/timeline/clips/:clipId", async (req, res) => {
  const projectId = req.query.projectId || req.body?.projectId;
  const ripple = String(req.query.ripple || req.body?.ripple || "true") !== "false";
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  for (const track of proj.timeline.tracks) {
    const i = track.clips.findIndex((c) => c.id === req.params.clipId);
    if (i >= 0) {
      const removed = track.clips[i];
      track.clips.splice(i, 1);
      if (ripple) rippleDelete(track, removed.start, removed.duration);
      proj.timeline.transitions = (proj.timeline.transitions || []).filter((tr) => tr.fromClipId !== removed.id && tr.toClipId !== removed.id);
      await saveProject(proj);
      return res.json({ ok: true, ripple });
    }
  }
  res.status(404).json({ error: "Clip not found" });
});
app.post("/api/timeline/effects", async (req, res) => {
  const { projectId, clipId, effectId, params = {} } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const found = findClip(proj, clipId);
  if (!found) return res.status(404).json({ error: "Clip not found" });
  const plugins = await loadPlugins();
  const plugin = plugins.find((p) => p.id === effectId);
  if (!plugin) return res.status(404).json({ error: "unknown effect", available: plugins.map((p) => p.id) });
  found.clip.effects = found.clip.effects || [];
  found.clip.effects.push({ id: randomUUID(), effectId, params: { ...params }, appliedAt: new Date().toISOString() });
  await saveProject(proj);
  res.json({ ok: true, clip: found.clip });
});
app.post("/api/timeline/transitions", async (req, res) => {
  const { projectId, fromClipId, toClipId, transitionId = "transition.crossfade", duration = 1 } = req.body || {};
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  if (!findClip(proj, fromClipId) || !findClip(proj, toClipId)) return res.status(404).json({ error: "Clip(s) not found" });
  const tr = { id: randomUUID(), transitionId, fromClipId, toClipId, duration: Number(duration) || 1 };
  proj.timeline.transitions = (proj.timeline.transitions || []).filter((x) => !(x.fromClipId === fromClipId && x.toClipId === toClipId));
  proj.timeline.transitions.push(tr);
  await saveProject(proj);
  res.json({ ok: true, transition: tr });
});
app.get("/api/preview/frame", async (req, res) => {
  const projectId = req.query.projectId;
  const t = parseFloat(req.query.t || "0");
  const proj = await readProject(projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const vTrack = findTrack(proj, "v1") || proj.timeline.tracks.find((x) => x.type === "video");
  const vClips = [...(vTrack?.clips || [])].sort((a, b) => a.start - b.start);
  if (!vClips.length) return res.status(400).json({ error: "No video clips" });
  const hit = resolveClipAtTime(vClips, t);
  if (!hit || !existsSync(hit.clip.sourcePath)) return res.status(400).json({ error: "No clip at time" });
  const out = join(PREVIEW_DIR, `${projectId}_${t.toFixed(2)}.jpg`);
  try {
    await execFileP("ffmpeg", ["-y", "-ss", String(Math.max(0, hit.sourceTime)), "-i", hit.clip.sourcePath, "-frames:v", "1", "-q:v", "3", out], { maxBuffer: 10e6 });
    res.type("image/jpeg").send(await fs.readFile(out));
  } catch (e) {
    res.status(500).json({ error: String(e.message || e) });
  }
});
app.get("/api/preview/info", async (req, res) => {
  const proj = await readProject(req.query.projectId);
  if (!proj) return res.status(404).json({ error: "no project" });
  const vTrack = findTrack(proj, "v1");
  const clips = [...(vTrack?.clips || [])].sort((a, b) => a.start - b.start);
  res.json({ duration: trackEnd(vTrack || { clips: [] }), clipCount: clips.length, clips: clips.map((c) => ({ id: c.id, start: c.start, duration: c.duration, filename: c.filename })) });
});
async function renderTimeline(proj, opts = {}) {
  const width = opts.width || 1280, height = opts.height || 720, jobId = opts.jobId || randomUUID();
  const outPath = opts.outputPath || join(RENDER_DIR, `${jobId}.mp4`);
  const vTrack = findTrack(proj, "v1") || proj.timeline.tracks.find((t) => t.type === "video");
  const aTrack = findTrack(proj, "a1") || proj.timeline.tracks.find((t) => t.type === "audio");
  const vClips = [...(vTrack?.clips || [])].sort((a, b) => a.start - b.start);
  if (!vClips.length) throw new Error("No video clips on timeline");
  const tmpDir = join(RENDER_DIR, `tmp_${jobId}`);
  await fs.mkdir(tmpDir, { recursive: true });
  const segmentPaths = [];
  for (let i = 0; i < vClips.length; i++) {
    const clip = vClips[i];
    if (!clip.sourcePath || !existsSync(clip.sourcePath)) throw new Error(`Missing source ${clip.id}`);
    const seg = join(tmpDir, `seg_${String(i).padStart(3, "0")}.mp4`);
    const dur = clip.duration || clip.outPoint - clip.inPoint;
    const vf = [`scale=${width}:${height}:force_original_aspect_ratio=decrease`, `pad=${width}:${height}:(ow-iw)/2:(oh-ih)/2`, "fps=30", "format=yuv420p"];
    for (const ef of clip.effects || []) {
      if (ef.effectId === "effect.fade_in") vf.push(`fade=t=in:st=0:d=${ef.params?.duration ?? 1}`);
      else if (ef.effectId === "effect.fade_out") {
        const d = ef.params?.duration ?? 1;
        vf.push(`fade=t=out:st=${Math.max(0, dur - d)}:d=${d}`);
      } else if (ef.effectId === "effect.scale") {
        const z = ef.params?.zoom ?? 1;
        if (z !== 1) vf.push(`scale=iw*${z}:ih*${z}`);
      } else if (ef.effectId === "effect.blur") vf.push(`boxblur=${ef.params?.amount ?? 5}:1`);
      else if (ef.effectId === "effect.brightness") vf.push(`eq=brightness=${ef.params?.value ?? 0}`);
      else if (ef.effectId === "effect.contrast") vf.push(`eq=contrast=${ef.params?.value ?? 1}`);
      else if (ef.effectId === "effect.crop") {
        const w = ef.params?.w ?? 1, h = ef.params?.h ?? 1;
        vf.push(`crop=iw*${w}:ih*${h}`);
      } else if (ef.effectId === "effect.title") {
        const text = String(ef.params?.text ?? "Title").replace(/:/g, "\\:").replace(/'/g, "");
        const fsz = ef.params?.fontsize ?? 48;
        vf.push(`drawtext=text='${text}':fontsize=${fsz}:fontcolor=white:x=(w-text_w)/2:y=h*0.08:box=1:boxcolor=black@0.4`);
      }
    }
    await execFileP("ffmpeg", ["-y", "-ss", String(clip.inPoint || 0), "-i", clip.sourcePath, "-t", String(dur), "-vf", vf.join(","), "-c:v", "libx264", "-an", seg], { maxBuffer: 20e6 });
    segmentPaths.push({ path: seg, clip, dur });
  }
  const transitions = proj.timeline.transitions || [];
  let silentVideo = join(tmpDir, "video_silent.mp4");
  const useXfade = segmentPaths.length >= 2 && transitions.some((tr) => tr.transitionId === "transition.crossfade");
  if (useXfade) {
    let current = segmentPaths[0].path, currentDur = segmentPaths[0].dur;
    for (let i = 1; i < segmentPaths.length; i++) {
      const prevClip = segmentPaths[i - 1].clip, nextClip = segmentPaths[i].clip;
      const tr = transitions.find((x) => x.fromClipId === prevClip.id && x.toClipId === nextClip.id);
      const fadeDur = Math.min(tr?.duration || 0, segmentPaths[i - 1].dur / 2, segmentPaths[i].dur / 2);
      const outSeg = join(tmpDir, `xf_${i}.mp4`);
      if (fadeDur > 0.05) {
        const offset = Math.max(0, currentDur - fadeDur);
        await execFileP("ffmpeg", ["-y", "-i", current, "-i", segmentPaths[i].path, "-filter_complex", `[0:v][1:v]xfade=transition=fade:duration=${fadeDur}:offset=${offset}[v]`, "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", outSeg], { maxBuffer: 30e6 });
        currentDur = currentDur + segmentPaths[i].dur - fadeDur; current = outSeg;
      } else {
