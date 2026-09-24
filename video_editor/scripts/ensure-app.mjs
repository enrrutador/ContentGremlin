import { existsSync, readFileSync, writeFileSync, readdirSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { gunzipSync } from "zlib";

const dir = join(dirname(fileURLToPath(import.meta.url)), "..");
const appPath = join(dir, "src", "app.js");
const payloadDir = join(dir, "payload");

if (existsSync(appPath)) {
  console.log("[ensure-app] src/app.js exists");
  process.exit(0);
}

if (!existsSync(payloadDir)) {
  console.error("[ensure-app] no src/app.js and no payload/");
  process.exit(1);
}

const files = readdirSync(payloadDir).filter((f) => f.endsWith(".b64")).sort();
const b64 = files.map((f) => readFileSync(join(payloadDir, f), "utf8")).join("").replace(/\s+/g, "");
let code = gunzipSync(Buffer.from(b64, "base64")).toString("utf8");

const old = `const __dirname = dirname(fileURLToPath(import.meta.url));\nconst MEDIA_DIR = join(__dirname, "media");\nconst PROJECTS_DIR = join(__dirname, "projects");\nconst PUBLIC_DIR = join(__dirname, "public");\nconst PLUGINS_DIR = join(__dirname, "plugins");\nconst RENDER_DIR = join(__dirname, "renders");\nconst PREVIEW_DIR = join(RENDER_DIR, "preview");\nconst JOBS_DIR = join(__dirname, "jobs");`;

const neu = `const __dirname = dirname(fileURLToPath(import.meta.url));\nconst ROOT = join(__dirname, "..");\nconst MEDIA_DIR = join(ROOT, "media");\nconst PROJECTS_DIR = join(ROOT, "projects");\nconst PUBLIC_DIR = join(ROOT, "public");\nconst PLUGINS_DIR = join(ROOT, "plugins");\nconst RENDER_DIR = join(ROOT, "renders");\nconst PREVIEW_DIR = join(RENDER_DIR, "preview");\nconst JOBS_DIR = join(ROOT, "jobs");`;

if (code.includes(old)) code = code.replace(old, neu);
code = code.replace(/from "\.\/lib\//g, 'from "../lib/');

mkdirSync(join(dir, "src"), { recursive: true });
writeFileSync(appPath, code);
console.log("[ensure-app] wrote src/app.js from payload", code.length, "bytes");
