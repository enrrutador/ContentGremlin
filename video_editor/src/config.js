import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
export const ROOT = join(__dirname, "..");
export const MEDIA_DIR = join(ROOT, "media");
export const PROJECTS_DIR = join(ROOT, "projects");
export const PUBLIC_DIR = join(ROOT, "public");
export const PLUGINS_DIR = join(ROOT, "plugins");
export const RENDER_DIR = join(ROOT, "renders");
export const PREVIEW_DIR = join(RENDER_DIR, "preview");
export const JOBS_DIR = join(ROOT, "jobs");
export const PORT = Number(process.env.PORT) || 3000;
