#!/usr/bin/env node
import { existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath, pathToFileURL } from "url";
import { spawnSync } from "child_process";

const dir = dirname(fileURLToPath(import.meta.url));
const run = (script) => {
  const r = spawnSync(process.execPath, [join(dir, "scripts", script)], { stdio: "inherit" });
  if (r.status !== 0) process.exit(r.status || 1);
};

run("assemble-routes.mjs");
run("ensure-app.mjs");

const appPath = join(dir, "src", "app.js");
if (!existsSync(appPath)) {
  console.error("[editor] missing src/app.js");
  process.exit(1);
}
console.log("[editor] modular → src/app.js");
await import(pathToFileURL(appPath).href);
