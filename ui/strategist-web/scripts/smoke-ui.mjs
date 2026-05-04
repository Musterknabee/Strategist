#!/usr/bin/env node
/**
 * Backward-compatible alias for smoke-frontend.mjs.
 */
import { runReadPlaneSmoke } from "./smoke-frontend.mjs";

const json = process.argv.includes("--json");
const baseFromEnv =
  process.env.STRATEGIST_SMOKE_API_BASE_URL?.trim() ||
  process.env.NEXT_PUBLIC_STRATEGIST_API_BASE_URL?.trim() ||
  "";

function normalizeBase(raw) {
  const s = String(raw || "")
    .trim()
    .replace(/\/+$/, "");
  if (!s) {
    throw new Error(
      "API base URL required: pass --api-base-url, argv position, or set STRATEGIST_SMOKE_API_BASE_URL",
    );
  }
  const u = new URL(s);
  if (u.protocol !== "http:" && u.protocol !== "https:") {
    throw new Error("API base must be http or https");
  }
  return s;
}

function parseBase() {
  const i = process.argv.indexOf("--api-base-url");
  if (i !== -1 && process.argv[i + 1]) return normalizeBase(process.argv[i + 1]);
  const pos = process.argv.filter((a) => a && !a.startsWith("-") && !a.endsWith(".mjs"));
  if (pos.length) return normalizeBase(pos[pos.length - 1]);
  return normalizeBase(baseFromEnv);
}

runReadPlaneSmoke({ base: parseBase(), json })
  .then((p) => process.exit(p.ok ? 0 : 1))
  .catch((e) => {
    process.stderr.write(`${e instanceof Error ? e.message : e}\n`);
    process.exit(1);
  });
