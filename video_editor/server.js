#!/usr/bin/env node
/**
 * ContentGremlin video_editor — Phase 3 full server
 * Decodes server.payload.b64 (gzip+base64) and runs the complete app.
 */
import { readFileSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath, pathToFileURL } from "url";
import { gunzipSync } from "zlib";

const dir = dirname(fileURLToPath(import.meta.url));
const payloadPath = join(dir, "server.payload.b64");
const built = join(dir, ".server_built.mjs");
const mono = join(dir, "server.monolith.js");

if (existsSync(mono) && process.env.USE_MONOLITH === "1") {
  await import(pathToFileURL(mono).href);
} else if (existsSync(payloadPath)) {
  const b64 = readFileSync(payloadPath, "utf8").replace(/\s+/g, "");
  const src = gunzipSync(Buffer.from(b64, "base64")).toString("utf8");
  writeFileSync(built, src);
  await import(pathToFileURL(built).href);
} else if (existsSync(mono)) {
  await import(pathToFileURL(mono).href);
} else {
  console.error("Missing server.payload.b64 (and server.monolith.js)");
  process.exit(1);
}
