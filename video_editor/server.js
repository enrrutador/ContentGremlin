#!/usr/bin/env node
/**
 * 1) source/*.js → assemble monolith
 * 2) server.monolith.js
 * 3) payload/*.b64 → unpack monolith
 */
import { readFileSync, writeFileSync, existsSync, readdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath, pathToFileURL } from "url";
import { gunzipSync } from "zlib";

const dir = dirname(fileURLToPath(import.meta.url));
const mono = join(dir, "server.monolith.js");
const srcDir = join(dir, "source");
const payloadDir = join(dir, "payload");

function assembleFromSource() {
  if (!existsSync(srcDir)) return false;
  const files = readdirSync(srcDir).filter((f) => f.endsWith(".js")).sort();
  if (!files.length) return false;
  writeFileSync(mono, files.map((f) => readFileSync(join(srcDir, f), "utf8")).join(""));
  console.log("[editor] assembled from source/", files.length, "parts");
  return true;
}

function unpackPayload() {
  if (!existsSync(payloadDir)) return false;
  const files = readdirSync(payloadDir).filter((f) => f.endsWith(".b64")).sort();
  if (!files.length) return false;
  const b64 = files.map((f) => readFileSync(join(payloadDir, f), "utf8")).join("").replace(/\s+/g, "");
  writeFileSync(mono, gunzipSync(Buffer.from(b64, "base64")).toString("utf8"));
  console.log("[editor] unpacked payload → server.monolith.js");
  return true;
}

if (existsSync(srcDir) && readdirSync(srcDir).some((f) => f.endsWith(".js"))) {
  assembleFromSource();
} else if (!existsSync(mono)) {
  if (!unpackPayload()) {
    console.error("[editor] Need source/, server.monolith.js, or payload/");
    process.exit(1);
  }
}

console.log("[editor] loading", mono);
await import(pathToFileURL(mono).href);
