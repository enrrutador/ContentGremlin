import { readFileSync, writeFileSync, readdirSync, existsSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { gunzipSync } from "zlib";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const bundle = join(root, "src", "bundle");
if (!existsSync(bundle)) process.exit(0);

const targets = {
  timeline: join(root, "src", "routes", "timeline.js"),
  agent: join(root, "src", "routes", "agent.js"),
  render: join(root, "src", "lib", "render.js"),
};

for (const [prefix, dest] of Object.entries(targets)) {
  if (existsSync(dest) && readFileSync(dest, "utf8").length > 100) continue;

  const parts = readdirSync(bundle)
    .filter((f) => f.startsWith(prefix + "_") && f.endsWith(".b64p"))
    .sort();
  if (parts.length) {
    const b64 = parts.map((f) => readFileSync(join(bundle, f), "utf8")).join("").replace(/\s+/g, "");
    const code = gunzipSync(Buffer.from(b64, "base64")).toString("utf8");
    mkdirSync(dirname(dest), { recursive: true });
    writeFileSync(dest, code);
    console.log("[assemble-routes]", dest, "from", parts.length, "b64p");
    continue;
  }

  const gz = join(bundle, `${prefix}.gz.b64`);
  if (existsSync(gz)) {
    const code = gunzipSync(Buffer.from(readFileSync(gz, "utf8").replace(/\s+/g, ""), "base64")).toString("utf8");
    mkdirSync(dirname(dest), { recursive: true });
    writeFileSync(dest, code);
    console.log("[assemble-routes]", dest, "from", prefix + ".gz.b64");
  }
}
