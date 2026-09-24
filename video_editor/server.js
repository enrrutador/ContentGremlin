#!/usr/bin/env node
import { readFileSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath, pathToFileURL } from "url";
const dir = dirname(fileURLToPath(import.meta.url));
const n = 16;
const parts = [];
for (let i = 0; i < n; i++) {
  const p = join(dir, `src/part${i}.js`);
  if (!existsSync(p)) { console.error("Missing", p); process.exit(1); }
  parts.push(readFileSync(p, "utf8"));
}
const built = join(dir, ".server_built.mjs");
writeFileSync(built, parts.join(""));
await import(pathToFileURL(built).href);
