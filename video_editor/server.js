#!/usr/bin/env node
/** Ensures src/app.js then loads modular app. */
import { existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath, pathToFileURL } from "url";
import { spawnSync } from "child_process";

const dir = dirname(fileURLToPath(import.meta.url));
const appPath = join(dir, "src", "app.js");
const ensure = join(dir, "scripts", "ensure-app.mjs");

if (!existsSync(appPath)) {
  const r = spawnSync(process.execPath, [ensure], { stdio: "inherit" });
  if (r.status !== 0) process.exit(r.status || 1);
}

console.log("[editor] modular → src/app.js");
await import(pathToFileURL(appPath).href);
