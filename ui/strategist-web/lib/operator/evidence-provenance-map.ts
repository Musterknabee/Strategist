/**
 * Deterministic labels for operator evidence strips (StatusBadge + tone alignment).
 */

const PENDING = "PENDING";
const UNKNOWN = "UNKNOWN";

/** Uppercase trimmed string or PENDING when absent. */
export function normalizeEvidenceField(raw: string | null | undefined): string {
  const t = (raw ?? "").trim();
  return t ? t.toUpperCase() : PENDING;
}

/** Trust / lineage / verification tokens → stable operator-facing badge text. */
export function normalizeTrustVerificationForBadge(raw: string | null | undefined): string {
  const u = normalizeEvidenceField(raw);
  if (u === PENDING) return PENDING;
  if (u === "TRUE" || u === "VERIFIED" || u === "1") return "VERIFIED";
  if (u === "FALSE" || u === "0" || u === "UNVERIFIED") return "UNVERIFIED";
  return u;
}

/** Snapshot verification boolean → badge string. */
export function projectionVerifiedLabel(verified: unknown): string {
  if (verified === true) return "VERIFIED";
  if (verified === false) return "UNVERIFIED";
  return PENDING;
}

/** Chain / ledger posture for operator actions index. */
export function chainIntegrityLabel(chainOk: boolean | null | undefined, issueCount: number | undefined): string {
  if (chainOk === true && (issueCount ?? 0) === 0) return "CHAIN_OK";
  if (chainOk === false) return "CHAIN_DEGRADED";
  if ((issueCount ?? 0) > 0) return "CHAIN_ISSUES";
  return UNKNOWN;
}
