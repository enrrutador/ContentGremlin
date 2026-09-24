#!/usr/bin/env node
/** Prefer server.monolith.js (single file). Fallback: join server.part0+1+2. */
import { readFileSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath, pathToFileURL } from "url";

const dir = dirname(fileURLToPath(import.meta.url));
const monolith = join(dir, "server.monolith.js");
if (existsSync(monolith)) {
  await import(pathToFileURL(monolith).href);
} else {
  const parts = ["server.part0.js", "server.part1.js", "server.part2.js"].map((p) => join(dir, p));
  for (const p of parts) {
    if (!existsSync(p)) {
      console.error(`Missing ${p} and no server.monolith.js`);
      process.exit(1);
    }
  }
  const built = join(dir, ".server_built.mjs");
  writeFileSync(built, parts.map((p) => readFileSync(p, "utf8")).join(""));
  await import(pathToFileURL(built).href);
}
