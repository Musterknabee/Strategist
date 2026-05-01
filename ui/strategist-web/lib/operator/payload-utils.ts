/**
 * Safe extraction helpers for backend read-plane payloads (unknown/dynamic tolerant).
 */

export function asRecord(v: unknown): Record<string, unknown> | null {
  return v !== null && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : null;
}

export function asString(v: unknown): string | undefined {
  return typeof v === "string" ? v : undefined;
}

export function asNumber(v: unknown): number | undefined {
  return typeof v === "number" && !Number.isNaN(v) ? v : undefined;
}

export function asBool(v: unknown): boolean | undefined {
  return typeof v === "boolean" ? v : undefined;
}

export function asStringArray(v: unknown): string[] {
  if (!Array.isArray(v)) return [];
  return v.filter((x): x is string => typeof x === "string");
}

/** Badge tone for operator status chips. */
export function classifyOperationalStatus(raw: string | undefined | null): "ok" | "warn" | "bad" | "neutral" {
  const u = (raw || "").toUpperCase();
  if (!u) return "neutral";
  if (["READY", "OK", "TRUE", "LIVE", "FRESH", "PASS", "HEALTHY"].includes(u)) return "ok";
  if (["BLOCKED", "FAIL", "FALSE", "ERROR", "STALE", "DEGRADED"].includes(u)) return "bad";
  if (u.includes("WARN") || u.includes("PENDING") || u.includes("LIMIT")) return "warn";
  return "neutral";
}

export function classifyProviderClassifiedStatus(classified: string | undefined | null): "ok" | "warn" | "bad" | "neutral" {
  const c = (classified || "").toUpperCase();
  if (c === "OK") return "ok";
  if (["AUTH_FAILED", "RATE_LIMITED", "PLAN_LIMITED"].includes(c)) return "bad";
  if (["PENDING_KEY", "PENDING_MANUAL_BROKER_SETUP", "NOT_CHECKED", "SKIPPED_NO_NETWORK"].includes(c)) return "warn";
  return "neutral";
}

/** Parse /readyz-style checks object into table rows (values may be booleans or nested objects). */
export function readinessCheckRows(checks: unknown): { key: string; ok: boolean | null; detail: string }[] {
  const o = asRecord(checks);
  if (!o) return [];
  return Object.entries(o).map(([key, val]) => {
    if (typeof val === "boolean") {
      return { key, ok: val, detail: "" };
    }
    const r = asRecord(val);
    const ok = r ? (asBool(r.ok) ?? null) : null;
    const detail =
      r && typeof r.detail === "string"
        ? r.detail
        : r && typeof r.message === "string"
          ? r.message
          : typeof val === "string"
            ? val
            : "";
    return { key, ok, detail };
  });
}

export type ReadinessBlockerRow = { code: string; message: string; remediation?: string };

/** Parse readiness blocker/warning objects from /readyz JSON. */
export function readinessBlockerRows(items: unknown): ReadinessBlockerRow[] {
  if (!Array.isArray(items)) return [];
  return items
    .map((item) => {
      const r = asRecord(item);
      if (!r) return null;
      const code = asString(r.code) ?? "—";
      const message = asString(r.message) ?? "";
      if (!message && code === "—") return null;
      const remediation = asString(r.remediation_hint);
      return { code, message, ...(remediation ? { remediation } : {}) };
    })
    .filter((x): x is ReadinessBlockerRow => x !== null);
}

/** Workboard queue length from payload (entries win over optional count). */
export function workboardQueueItemCount(payload: { queue?: { entries?: unknown[]; work_item_count?: number } } | null | undefined): number | null {
  if (!payload?.queue) return null;
  const n = asNumber(payload.queue.work_item_count);
  const ent = payload.queue.entries;
  if (Array.isArray(ent)) return ent.length;
  if (n !== undefined) return n;
  return null;
}

/** True if any registry artifact path string matches (case-insensitive substring). */
export function evidenceRegistryHasPathHint(registryTable: unknown, needle: string): boolean {
  const low = needle.toLowerCase();
  if (!Array.isArray(registryTable)) return false;
  for (const row of registryTable) {
    const r = asRecord(row);
    const p = r && asString(r.path);
    if (p && p.toLowerCase().includes(low)) return true;
  }
  return false;
}
