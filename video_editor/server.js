#!/usr/bin/env node
/** Prefers server.monolith.js; payload/*.b64 is optional fallback. */
import { readFileSync, writeFileSync, existsSync, readdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath, pathToFileURL } from "url";
import { gunzipSync } from "zlib";

const dir = dirname(fileURLToPath(import.meta.url));
const mono = join(dir, "server.monolith.js");
const built = join(dir, ".server_built.mjs");
const payloadDir = join(dir, "payload");

function loadFromPayload() {
  if (!existsSync(payloadDir)) return null;
  const files = readdirSync(payloadDir).filter((f) => f.endsWith(".b64")).sort();
  if (!files.length) return null;
  return files.map((f) => readFileSync(join(payloadDir, f), "utf8")).join("").replace(/\s+/g, "");
}

const forcePayload = process.env.USE_PAYLOAD === "1";

if (!forcePayload && existsSync(mono)) {
  console.log("[editor] loading server.monolith.js");
  await import(pathToFileURL(mono).href);
} else {
  const b64 = loadFromPayload();
  if (b64) {
    console.log("[editor] loading from payload/*.b64");
    writeFileSync(built, gunzipSync(Buffer.from(b64, "base64")).toString("utf8"));
    await import(pathToFileURL(built).href);
  } else if (existsSync(mono)) {
    await import(pathToFileURL(mono).href);
  } else {
    console.error("[editor] Missing server.monolith.js and payload/*.b64");
    process.exit(1);
  }
}
