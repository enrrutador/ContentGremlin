#!/usr/bin/env node
import { readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath, pathToFileURL } from "url";
const dir = dirname(fileURLToPath(import.meta.url));
const built = join(dir, ".server_built.mjs");
const parts = ["server.part0.js", "server.part1.js", "server.part2.js"].map((p) => join(dir, p));
const body = parts.map((p) => readFileSync(p, "utf8")).join("");
writeFileSync(built, body);
await import(pathToFileURL(built).href);
