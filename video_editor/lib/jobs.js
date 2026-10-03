/** Persist render jobs to disk */
import { promises as fs } from "fs";
import { join } from "path";

export function createJobStore(jobsDir) {
  function isSafeJobId(id) {
    return typeof id === "string" && /^[A-Za-z0-9_-]{1,64}$/.test(id);
  }
  async function ensure() {
    await fs.mkdir(jobsDir, { recursive: true });
  }
  async function save(job) {
    if (!job || !isSafeJobId(job.jobId)) throw new Error("jobId inválido");
    await ensure();
    await fs.writeFile(join(jobsDir, `${job.jobId}.json`), JSON.stringify(job, null, 2));
    return job;
  }
  async function get(jobId) {
    if (!isSafeJobId(jobId)) return null;
    try {
      return JSON.parse(await fs.readFile(join(jobsDir, `${jobId}.json`), "utf-8"));
    } catch {
      return null;
    }
  }
  async function list(limit = 50) {
    await ensure();
    const files = (await fs.readdir(jobsDir)).filter((f) => f.endsWith(".json"));
    const jobs = [];
    for (const f of files.slice(-limit)) {
      try {
        jobs.push(JSON.parse(await fs.readFile(join(jobsDir, f), "utf-8")));
      } catch {}
    }
    return jobs.sort((a, b) => String(b.updatedAt || "").localeCompare(String(a.updatedAt || "")));
  }
  return { save, get, list };
}
