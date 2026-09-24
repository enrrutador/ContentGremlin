#!/usr/bin/env node
/**
 * ContentGremlin video_editor entrypoint.
 * Joins server.part{0,1,2}.js and runs the full app.
 * Source of truth for logic: the three part files (concatenated = full server).
 */
import { readFileSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath, pathToFileURL } from "url";

const dir = dirname(fileURLToPath(import.meta.url));
const partNames = ["server.part0.js", "server.part1.js", "server.part2.js"];
const parts = partNames.map((p) => join(dir, p));
for (const p of parts) {
  if (!existsSync(p)) {
    console.error(`Missing ${p}. Restore server.part*.js from the repo.`);
    process.exit(1);
  }
}
const built = join(dir, ".server_built.mjs");
writeFileSync(built, parts.map((p) => readFileSync(p, "utf8")).join(""));
await import(pathToFileURL(built).href);
