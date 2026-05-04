#!/usr/bin/env node
/**
 * Frontend read-plane smoke (no browser, no API token).
 * Verifies API reachability + JSON shape. Does NOT claim production frontend readiness.
 *
 * Usage:
 *   node scripts/smoke-frontend.mjs --api-base-url http://127.0.0.1:8000 --json
 *   STRATEGIST_SMOKE_API_BASE_URL=http://127.0.0.1:8000 node scripts/smoke-frontend.mjs
 *   NEXT_PUBLIC_STRATEGIST_API_BASE_URL=http://127.0.0.1:8000 node scripts/smoke-frontend.mjs
 *
 * Optional: checks .next/BUILD_ID when present (run `npm run build` first).
 */
import { access } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const _webRoot = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");

function normalizeBase(raw) {
  const s = String(raw || "")
    .trim()
    .replace(/\/+$/, "");
  if (!s) {
    throw new Error(
      "API base URL required: pass --api-base-url, or set STRATEGIST_SMOKE_API_BASE_URL / NEXT_PUBLIC_STRATEGIST_API_BASE_URL",
    );
  }
  const u = new URL(s);
  if (u.protocol !== "http:" && u.protocol !== "https:") {
    throw new Error("API base must be http or https");
  }
  return s;
}

function parseArgv(argv) {
  let json = argv.includes("--json");
  let base =
    process.env.STRATEGIST_SMOKE_API_BASE_URL?.trim() ||
    process.env.NEXT_PUBLIC_STRATEGIST_API_BASE_URL?.trim() ||
    "";
  const i = argv.indexOf("--api-base-url");
  if (i !== -1 && argv[i + 1]) base = String(argv[i + 1]).trim();
  if (!base) {
    const pos = argv.filter((a) => a && !a.startsWith("-") && !a.endsWith(".mjs"));
    if (pos.length) base = pos[pos.length - 1];
  }
  return { base: normalizeBase(base), json };
}

async function fetchJson(url) {
  const res = await fetch(url, { method: "GET", headers: { accept: "application/json" } });
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }
  return { res, data, text };
}

export async function runReadPlaneSmoke({ base, json }) {
  const errors = [];

  const facadeUrl = new URL("/ui/facade", base + "/").toString();
  const workboardUrl = new URL("/ui/workboard?board_label=operator", base + "/").toString();

  let facade;
  try {
    facade = await fetchJson(facadeUrl);
  } catch (e) {
    errors.push(`facade fetch: ${e instanceof Error ? e.message : e}`);
    facade = null;
  }

  if (facade && !facade.res.ok) {
    errors.push(`facade HTTP ${facade.res.status}`);
  }
  if (facade && facade.data) {
    if (typeof facade.data.schema_version !== "string") {
      errors.push("facade: missing schema_version");
    }
    if (!Array.isArray(facade.data.routes)) {
      errors.push("facade: routes must be an array");
    }
  } else if (facade && !errors.some((m) => m.startsWith("facade fetch"))) {
    errors.push("facade: invalid JSON");
  }

  let workboard;
  try {
    workboard = await fetchJson(workboardUrl);
  } catch (e) {
    errors.push(`workboard fetch: ${e instanceof Error ? e.message : e}`);
    workboard = null;
  }

  if (workboard && !workboard.res.ok) {
    errors.push(`workboard HTTP ${workboard.res.status}`);
  }
  if (workboard && workboard.data) {
    if (workboard.data.schema_version !== "ui_workboard_dashboard/v1") {
      errors.push(`workboard: unexpected schema_version ${workboard.data.schema_version}`);
    }
    if (!workboard.data.stats || typeof workboard.data.stats !== "object") {
      errors.push("workboard: missing stats");
    }
  } else if (workboard && !errors.some((m) => m.startsWith("workboard fetch"))) {
    errors.push("workboard: invalid JSON");
  }

  let buildOk = false;
  try {
    await access(path.join(_webRoot, ".next", "BUILD_ID"));
    buildOk = true;
  } catch {
    buildOk = false;
  }

  const ok = errors.length === 0;
  const payload = {
    schema_version: "strategist_frontend_smoke/v1",
    ok,
    disclaimer: "Read-plane reachability only; does not certify frontend production readiness (NOT_CLAIMED).",
    api_base: base,
    facade_http: facade?.res?.status ?? null,
    workboard_http: workboard?.res?.status ?? null,
    next_build_present: buildOk,
    errors,
  };

  if (json) {
    process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
  } else if (ok) {
    process.stdout.write(`frontend smoke OK: ${base}\n`);
  } else {
    process.stderr.write(`frontend smoke FAIL: ${errors.join("; ")}\n`);
  }

  return payload;
}

async function cliMain() {
  const { base, json } = parseArgv(process.argv);
  const payload = await runReadPlaneSmoke({ base, json });
  process.exit(payload.ok ? 0 : 1);
}

const invokedAsSmokeFrontend = Boolean(
  process.argv[1]?.replace(/\\/g, "/").endsWith("smoke-frontend.mjs"),
);
if (invokedAsSmokeFrontend) {
  cliMain().catch((e) => {
    process.stderr.write(`${e instanceof Error ? e.message : e}\n`);
    process.exit(1);
  });
}
