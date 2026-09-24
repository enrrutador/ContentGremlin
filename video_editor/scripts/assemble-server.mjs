import { readFileSync, writeFileSync, readdirSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
const dir = join(dirname(fileURLToPath(import.meta.url)), "..");
const srcDir = join(dir, "source");
const out = join(dir, "server.monolith.js");
if (!existsSync(srcDir)) {
  console.error("missing source/");
  process.exit(1);
}
const files = readdirSync(srcDir).filter((f) => f.endsWith(".js")).sort();
const body = files.map((f) => readFileSync(join(srcDir, f), "utf8")).join("");
writeFileSync(out, body);
console.log("[assemble] server.monolith.js", body.length, "bytes from", files.length, "parts");
