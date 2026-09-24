#!/usr/bin/env node
/**
 * Phase 3 full server: joins server.payload.1.b64 + server.payload.2.b64,
 * gunzips, and runs the complete application.
 */
import { readFileSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath, pathToFileURL } from "url";
import { gunzipSync } from "zlib";

const dir = dirname(fileURLToPath(import.meta.url));
const p1 = join(dir, "server.payload.1.b64");
const p2 = join(dir, "server.payload.2.b64");
const single = join(dir, "server.payload.b64");
const mono = join(dir, "server.monolith.js");
const built = join(dir, ".server_built.mjs");

function loadB64() {
  if (existsSync(p1) && existsSync(p2)) {
    return (readFileSync(p1, "utf8") + readFileSync(p2, "utf8")).replace(/\s+/g, "");
  }
  if (existsSync(single)) return readFileSync(single, "utf8").replace(/\s+/g, "");
  return null;
}

if (existsSync(mono) && process.env.USE_MONOLITH === "1") {
  await import(pathToFileURL(mono).href);
} else {
  const b64 = loadB64();
  if (!b64) {
    if (existsSync(mono)) {
      await import(pathToFileURL(mono).href);
    } else {
      console.error("Missing server.payload.1.b64 + server.payload.2.b64");
      process.exit(1);
    }
  } else {
    const src = gunzipSync(Buffer.from(b64, "base64")).toString("utf8");
    writeFileSync(built, src);
    await import(pathToFileURL(built).href);
  }
}
