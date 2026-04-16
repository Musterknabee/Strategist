#!/usr/bin/env node
import { existsSync, rmSync } from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const artifactsDir = path.join(root, "artifacts");
const targets = [
  path.join(artifactsDir, "frontend-diagnostics.snapshot.json"),
  path.join(artifactsDir, "frontend-diagnostics.history.jsonl"),
];

const removed = [];
const missing = [];
for (const target of targets) {
  if (existsSync(target)) {
    rmSync(target, { force: true });
    removed.push(path.relative(root, target));
  } else {
    missing.push(path.relative(root, target));
  }
}

console.log("Strategist frontend diagnostics reset");
console.log(`Removed: ${removed.length}`);
for (const file of removed) console.log(`  - ${file}`);
if (missing.length) {
  console.log(`Already absent: ${missing.length}`);
  for (const file of missing) console.log(`  - ${file}`);
}
console.log("Next step: run npm run export:diagnostics after your next local bring-up pass.");
