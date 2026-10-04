import { promises as fs } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const dir = join(dirname(fileURLToPath(import.meta.url)), "..");
const MAX_AGE_MS = 7 * 24 * 3600 * 1000;

async function prune(sub, olderThanMs, keep = 0) {
  const target = join(dir, sub);
  let removed = 0;
  try {
    const files = await fs.readdir(target);
    const now = Date.now();
    for (const f of files) {
      const p = join(target, f);
      try {
        const st = await fs.stat(p);
        if (!st.isFile()) continue;
        if (now - st.mtimeMs > olderThanMs) {
          await fs.unlink(p);
          removed++;
        }
      } catch {}
    }
  } catch {}
  if (removed) console.log(`[prune] ${sub}: ${removed} archivos viejos eliminados`);
}

await prune("jobs", MAX_AGE_MS);
await prune("renders/preview", MAX_AGE_MS);
