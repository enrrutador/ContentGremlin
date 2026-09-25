import { readFileSync, writeFileSync, readdirSync, existsSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
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
    .filter((f) => f.startsWith(prefix + "_") && f.endsWith(".js.txt"))
    .sort();
  if (!parts.length) continue;
  mkdirSync(dirname(dest), { recursive: true });
  writeFileSync(dest, parts.map((f) => readFileSync(join(bundle, f), "utf8")).join(""));
  console.log("[assemble-routes]", dest, "from", parts.length, "parts");
}
