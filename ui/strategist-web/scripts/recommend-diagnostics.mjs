#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";

const historyPath = path.join(process.cwd(), "artifacts", "frontend-diagnostics.history.jsonl");

async function readHistory() {
  try {
    const raw = await fs.readFile(historyPath, "utf8");
    return raw
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => JSON.parse(line))
      .sort((a, b) => (a.generatedAt < b.generatedAt ? 1 : -1));
  } catch (error) {
    if (error && error.code === "ENOENT") return [];
    throw error;
  }
}

const history = await readHistory();
if (!history.length) {
  console.log("No diagnostics history exists yet.");
  console.log("Next: npm run bootstrap:env && npm install && npm run doctor && npm run dev");
  console.log("Then: npm run smoke && npm run export:diagnostics && npm run summarize:diagnostics");
  process.exit(0);
}

const latest = history[0];
const warningRuns = history.filter((entry) => entry.posture === "warning").length;
const attentionRuns = history.filter((entry) => entry.posture === "attention").length;

console.log(`Latest posture: ${latest.posture} (${latest.mode}) @ ${latest.generatedAt}`);
if (latest.posture !== "ok") {
  console.log("Recommended: npm run doctor && npm run smoke && npm run export:diagnostics");
}
if (warningRuns || attentionRuns) {
  console.log(`Recent warning/attention runs: ${warningRuns}/${attentionRuns}`);
  console.log("Recommended: npm run summarize:diagnostics && npm run prune:diagnostics");
}
console.log("Maintenance loop: npm run doctor && npm run dev && npm run smoke && npm run export:diagnostics && npm run summarize:diagnostics");
