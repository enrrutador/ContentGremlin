/** Timeline render — concat seguro con FFmpeg */
import { promises as fs } from "fs";
import { join, basename } from "path";
import { randomUUID } from "crypto";
import { execFileP, videoEncoderArgs } from "./media.js";

function resolveSource(proj, clip) {
  if (clip.sourcePath) return clip.sourcePath;
  if (clip.path) return clip.path;
  if (clip.mediaId && Array.isArray(proj.media)) {
    const m = proj.media.find((x) => x.id === clip.mediaId);
    if (m) return m.path || m.sourcePath || null;
  }
  return null;
}

export async function renderTimelineSafe(proj, opts = {}) {
  const {
    jobId = randomUUID().slice(0, 8),
    width = 1280,
    height = 720,
    outputPath = null,
    useHwAccel = false,
    RENDER_DIR = "/tmp",
    onProgress = null,
  } = opts;

  await fs.mkdir(RENDER_DIR, { recursive: true });
  const out = outputPath || join(RENDER_DIR, `render_${jobId}.mp4`);

  const tracks = proj?.timeline?.tracks || [];
  const vTracks = tracks.filter((t) => t.type !== "audio");
  let clips = [];
  for (const t of vTracks) for (const c of t.clips || []) clips.push(c);
  clips.sort((a, b) => (a.start || 0) - (b.start || 0));

  const report = async (percent, phase) => {
    try { await onProgress?.({ percent, phase }); } catch {}
  };

  await report(5, "prepare");

  const sources = [];
  for (const c of clips) {
    const src = resolveSource(proj, c);
    if (src) {
      try {
        await fs.access(src);
        sources.push({ clip: c, src });
      } catch {}
    }
  }

  // Sin clips válidos: video placeholder 5s
  if (!sources.length) {
    await report(30, "placeholder");
    const safeName = String(proj?.name || "Gremlin").replace(/'/g, "").slice(0, 60);
    await execFileP("ffmpeg", [
      "-y",
      "-f", "lavfi", "-i", `color=c=0x1a1a2e:s=${width}x${height}:d=5:r=30`,
      "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo:d=5",
      "-vf", `drawtext=text='${safeName}':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2`,
      "-shortest",
      ...videoEncoderArgs(false),
      "-c:a", "aac", "-b:a", "128k",
      out,
    ], { maxBuffer: 20e6 });
    await report(100, "done");
    return { outputPath: out, url: `/renders/${basename(out)}`, segments: 0, xfade: false };
  }

  await report(20, "concat");
  // Lista concat demuxer
  const listFile = join(RENDER_DIR, `.concat_${jobId}.txt`);
  const lines = sources.map(({ src }) => {
    const esc = String(src).replace(/'/g, "'\\''");
    return `file '${esc}'`;
  });
  await fs.writeFile(listFile, lines.join("\n"), "utf-8");

  try {
    await report(50, "encode");
    // Concat + escala/pad + aac. Recorte por inPoint/duration se aplica por clip
    // vía -ss/-t por input sería ideal, pero para MVP concatenamos archivos completos
    // y limitamos a duraciones de timeline con -t total.
    const totalDur = clips.reduce((m, c) => Math.max(m, (c.start || 0) + (c.duration || 0)), 0);
    const args = [
      "-y", "-f", "concat", "-safe", "0", "-i", listFile,
      "-vf", `scale=${width}:${height}:force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1,pad=${width}:${height}:(ow-iw)/2:(oh-ih)/2`,
      ...videoEncoderArgs(useHwAccel),
      "-c:a", "aac", "-b:a", "128k",
    ];
    if (totalDur > 0 && Number.isFinite(totalDur)) {
      args.push("-t", String(Math.min(totalDur, 600)));
    }
    args.push(out);
    await execFileP("ffmpeg", args, { maxBuffer: 20e6 });
  } catch (e) {
    // Fallback sin hwaccel si falló con GPU
    if (useHwAccel) {
      const args = [
        "-y", "-f", "concat", "-safe", "0", "-i", listFile,
        "-vf", `scale=${width}:${height}:force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1,pad=${width}:${height}:(ow-iw)/2:(oh-ih)/2`,
        ...videoEncoderArgs(false),
        "-c:a", "aac", "-b:a", "128k", out,
      ];
      await execFileP("ffmpeg", args, { maxBuffer: 20e6 });
    } else {
      throw e;
    }
  } finally {
    try { await fs.unlink(listFile); } catch {}
  }

  await report(100, "done");
  return {
    outputPath: out,
    url: `/renders/${basename(out)}`,
    segments: sources.length,
    xfade: false,
  };
}
