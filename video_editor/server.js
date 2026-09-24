#!/usr/bin/env node
import { readFileSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath, pathToFileURL } from "url";
import { gunzipSync } from "zlib";
const dir = dirname(fileURLToPath(import.meta.url));
const payload = join(dir, "server.payload.b64");
const pa = join(dir, "server.payload.a.b64");
const pb = join(dir, "server.payload.b.b64");
const mono = join(dir, "server.monolith.js");
const built = join(dir, ".server_built.mjs");
function loadB64() {
  if (existsSync(pa) && existsSync(pb))
    return (readFileSync(pa, "utf8") + readFileSync(pb, "utf8")).replace(/\s+/g, "");
  if (existsSync(payload)) return readFileSync(payload, "utf8").replace(/\s+/g, "");
  return null;
}
if (existsSync(mono) && process.env.USE_MONOLITH === "1") {
  await import(pathToFileURL(mono).href);
} else {
  const b64 = loadB64();
  if (b64) {
    writeFileSync(built, gunzipSync(Buffer.from(b64, "base64")).toString("utf8"));
    await import(pathToFileURL(built).href);
  } else if (existsSync(mono)) {
    await import(pathToFileURL(mono).href);
  } else {
    console.error("Missing server.payload.b64 or server.monolith.js");
    process.exit(1);
  }
}
