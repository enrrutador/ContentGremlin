#!/usr/bin/env node
/** Phase 3: join server.payload.{0,1,2,3}.b64 → gunzip → run */
import { readFileSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath, pathToFileURL } from "url";
import { gunzipSync } from "zlib";

const dir = dirname(fileURLToPath(import.meta.url));
const parts = [0, 1, 2, 3].map((i) => join(dir, `server.payload.${i}.b64`));
const mono = join(dir, "server.monolith.js");
const built = join(dir, ".server_built.mjs");

if (existsSync(mono) && process.env.USE_MONOLITH === "1") {
  await import(pathToFileURL(mono).href);
} else if (parts.every((p) => existsSync(p))) {
  const b64 = parts.map((p) => readFileSync(p, "utf8")).join("").replace(/\s+/g, "");
  writeFileSync(built, gunzipSync(Buffer.from(b64, "base64")).toString("utf8"));
  await import(pathToFileURL(built).href);
} else if (existsSync(mono)) {
  await import(pathToFileURL(mono).href);
} else {
  console.error("Missing server.payload.0-3.b64");
  process.exit(1);
}
