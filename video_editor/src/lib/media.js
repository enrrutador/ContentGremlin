import { execFile } from "child_process";
import { promisify } from "util";
import { promises as fs } from "fs";
import { join } from "path";
import { PLUGINS_DIR } from "../config.js";

export const execFileP = promisify(execFile);

export function videoEncoderArgs(useHwAccel) {
  if (useHwAccel) {
    return ["-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", "23"];
  }
  return ["-c:v", "libx264", "-preset", "medium", "-crf", "20"];
}

export async function probeMedia(filePath) {
  try {
    const { stdout } = await execFileP(
      "ffprobe",
      ["-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", filePath],
      { maxBuffer: 5e6 }
    );
    const info = JSON.parse(stdout);
    const duration = parseFloat(info.format?.duration || 0) || 0;
    const video = (info.streams || []).find((s) => s.codec_type === "video");
    const audio = (info.streams || []).find((s) => s.codec_type === "audio");
    return {
      duration,
      width: video?.width || null,
      height: video?.height || null,
      hasVideo: !!video,
      hasAudio: !!audio,
      codec: video?.codec_name || audio?.codec_name || null,
    };
  } catch (e) {
    return {
      duration: 0,
      width: null,
      height: null,
      hasVideo: false,
      hasAudio: false,
      codec: null,
      probeError: String(e.message || e),
    };
  }
}

export async function loadPlugins() {
  const plugins = [];
  try {
    for (const f of await fs.readdir(join(PLUGINS_DIR, "examples"))) {
      if (!f.endsWith(".json")) continue;
      try {
        plugins.push(JSON.parse(await fs.readFile(join(PLUGINS_DIR, "examples", f), "utf-8")));
      } catch {}
    }
  } catch {}
  return plugins;
}
