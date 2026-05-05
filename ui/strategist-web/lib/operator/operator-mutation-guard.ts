import { asBool, asRecord, asString } from "@/lib/operator/payload-utils";
import type { UiMutationSafetyStatus } from "@/lib/api/types";

/** Parse GET /ui/runtime `mutation_safety` object (read-plane; no secrets). */
export function parseMutationSafety(raw: unknown): UiMutationSafetyStatus | null {
  const r = asRecord(raw);
  if (!r) return null;
  const mode = asString(r.authorization_mode);
  if (!mode) return null;
  return {
    runtime_mode: asString(r.runtime_mode) ?? "UNKNOWN",
    authorization_mode: mode,
    token_configured: asBool(r.token_configured) === true,
    mutation_routes_safe: asBool(r.mutation_routes_safe) === true,
    detail_code: asString(r.detail_code) ?? "UNKNOWN",
  };
}

export function mutationSurfaceAllowed(safety: UiMutationSafetyStatus | null): { ok: boolean; reason: string } {
  if (!safety) return { ok: false, reason: "MUTATION_SAFETY_UNKNOWN" };
  if (!safety.mutation_routes_safe) return { ok: false, reason: safety.detail_code };
  return { ok: true, reason: "" };
}

/** Browser must supply a token when backend is token-protected (production-style). */
export function mutationRequiresBrowserToken(safety: UiMutationSafetyStatus | null): boolean {
  if (!safety || !safety.mutation_routes_safe) return false;
  return safety.authorization_mode === "TOKEN_PROTECTED";
}
