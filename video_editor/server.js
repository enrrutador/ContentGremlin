#!/usr/bin/env node
/** Full Phase 3 server = server.monolith.A.js + server.monolith.B.js */
import { readFileSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath, pathToFileURL } from "url";

const dir = dirname(fileURLToPath(import.meta.url));
const a = join(dir, "server.monolith.A.js");
const b = join(dir, "server.monolith.B.js");
const mono = join(dir, "server.monolith.js");

if (existsSync(mono) && !process.env.FORCE_PARTS) {
  await import(pathToFileURL(mono).href);
} else if (existsSync(a) && existsSync(b)) {
  const built = join(dir, ".server_built.mjs");
  writeFileSync(built, readFileSync(a, "utf8") + readFileSync(b, "utf8"));
  await import(pathToFileURL(built).href);
} else {
  console.error("Need server.monolith.js or server.monolith.A.js + server.monolith.B.js");
  process.exit(1);
}
