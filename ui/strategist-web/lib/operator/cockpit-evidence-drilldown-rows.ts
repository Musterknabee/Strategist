/**
 * Read-plane row builders for Research OS status aggregate and paper execution cockpit drilldowns.
 */
import { asRecord, asString } from "@/lib/operator/payload-utils";

export type EvidenceDrilldownRow = {
  __id: string;
  surface: string;
  status: string;
  trust: string;
  blockers: number;
  warnings: number;
  at: string;
  digestPreview: string;
  digestFull?: string | null;
  raw: unknown;
};

const UNKNOWN = "UNKNOWN";
const PENDING = "PENDING";

function arrLen(v: unknown): number {
  return Array.isArray(v) ? v.length : 0;
}

function degradedCount(rec: Record<string, unknown> | null): number {
  if (!rec) return 0;
  const d = rec.degraded;
  return Array.isArray(d) ? d.length : 0;
}

function pickLatest(rec: Record<string, unknown> | null): Record<string, unknown> | null {
  if (!rec) return null;
  return asRecord(rec.latest) ?? rec;
}

function pickStatus(rec: Record<string, unknown> | null, latest: Record<string, unknown> | null): string {
  if (!rec) return UNKNOWN;
  const top = asString(rec.status);
  if (top === "NOT_PRESENT") return "NOT_PRESENT";
  const l = latest;
  return (
    asString(l?.status) ??
    asString(l?.drift_status) ??
    asString(l?.decision) ??
    asString(l?.verification_status) ??
    asString(l?.closure_status) ??
    asString(l?.release_readiness_status) ??
    asString(l?.policy_gate_status) ??
    asString(l?.exception_status) ??
    asString(l?.remediation_status) ??
    top ??
    UNKNOWN
  );
}

function pickTrust(rec: Record<string, unknown> | null, latest: Record<string, unknown> | null): string {
  const l = latest ?? rec;
  return (
    asString(l?.trust_banner) ??
    asString(l?.closure_trust_banner) ??
    asString(rec?.trust_banner) ??
    UNKNOWN
  );
}

function pickBlkWrn(rec: Record<string, unknown> | null, latest: Record<string, unknown> | null): { blk: number; wrn: number } {
  if (!rec) return { blk: 0, wrn: 0 };
  const l = latest ?? rec;
  const blk =
    arrLen(l?.blockers) +
    arrLen(rec.blockers) +
    (typeof l?.blocker_count === "number" ? (l.blocker_count as number) : 0) +
    degradedCount(rec);
  const wrn = arrLen(l?.warnings) + arrLen(rec.warnings) + (typeof l?.warning_count === "number" ? (l.warning_count as number) : 0);
  return { blk, wrn };
}

function pickDigest(latest: Record<string, unknown> | null): { preview: string; full?: string | null } {
  if (!latest) return { preview: PENDING };
  const full =
    asString(latest.manifest_sha256) ??
    asString(latest.bundle_sha256) ??
    asString(latest.artifact_sha256) ??
    asString(latest.report_sha256) ??
    undefined;
  const preview = full ? full.slice(0, 18) : PENDING;
  return { preview, full: full ?? null };
}

function pickAt(rec: Record<string, unknown> | null): string {
  return asString(rec?.generated_at_utc) ?? PENDING;
}

function researchAttestationRow(rec: unknown): EvidenceDrilldownRow {
  const r = asRecord(rec);
  if (!r) {
    return {
      __id: "ros:attestation",
      surface: "Attestation / verification",
      status: UNKNOWN,
      trust: UNKNOWN,
      blockers: 0,
      warnings: 0,
      at: PENDING,
      digestPreview: PENDING,
      digestFull: null,
      raw: null,
    };
  }
  const ver = asRecord(r.latest_verification);
  const att = asRecord(r.latest_attestation);
  const status =
    [asString(ver?.status), asString(att?.decision)].filter(Boolean).join(" · ") ||
    asString(r.status) ||
    UNKNOWN;
  const trust = asString(ver?.trust_banner) ?? asString(att?.closure_trust_banner) ?? asString(r.trust_banner) ?? UNKNOWN;
  const blk = arrLen(ver?.blockers) + arrLen(att?.blockers) + degradedCount(r);
  const wrn = arrLen(ver?.warnings) + arrLen(att?.warnings);
  const dig = pickDigest(ver ?? att);
  return {
    __id: "ros:attestation",
    surface: "Attestation / verification",
    status,
    trust,
    blockers: blk,
    warnings: wrn,
    at: pickAt(r),
    digestPreview: dig.preview,
    digestFull: asString(ver?.manifest_sha256_expected) ?? asString(ver?.result_sha256) ?? dig.full,
    raw: rec,
  };
}

function researchRow(id: string, surface: string, rec: unknown): EvidenceDrilldownRow {
  const r = asRecord(rec);
  const latest = pickLatest(r);
  const { blk, wrn } = pickBlkWrn(r, latest);
  const dig = pickDigest(latest);
  return {
    __id: `ros:${id}`,
    surface,
    status: pickStatus(r, latest),
    trust: pickTrust(r, latest),
    blockers: blk,
    warnings: wrn,
    at: pickAt(r),
    digestPreview: dig.preview,
    digestFull: dig.full,
    raw: rec,
  };
}

const RESEARCH_OS_SURFACES: { id: string; label: string; key: string }[] = [
  { id: "closure", label: "Closure manifest", key: "research_os_closure_latest" },
  { id: "attestation", label: "Attestation / verification", key: "research_os_attestation_latest" },
  { id: "drift", label: "Evidence drift", key: "research_os_evidence_drift_latest" },
  { id: "policy_gate", label: "Policy gate", key: "research_os_policy_gate_latest" },
  { id: "release_readiness", label: "Release readiness", key: "research_os_release_readiness_latest" },
  { id: "exceptions", label: "Exceptions", key: "research_os_exception_latest" },
  { id: "remediation", label: "Remediation", key: "research_os_remediation_latest" },
];

export function buildResearchOsEvidenceRows(statusRoot: Record<string, unknown> | null): EvidenceDrilldownRow[] {
  if (!statusRoot) {
    return RESEARCH_OS_SURFACES.map(({ id, label }) => ({
      __id: `ros:${id}`,
      surface: label,
      status: UNKNOWN,
      trust: UNKNOWN,
      blockers: 0,
      warnings: 0,
      at: PENDING,
      digestPreview: PENDING,
      digestFull: null,
      raw: null,
    }));
  }
  return RESEARCH_OS_SURFACES.map(({ id, label, key }) =>
    id === "attestation" ? researchAttestationRow(statusRoot[key]) : researchRow(id, label, statusRoot[key]),
  );
}

function paperRow(
  id: string,
  surface: string,
  raw: unknown,
  status: string,
  trust: string,
  blk: number,
  wrn: number,
  at: string,
  digestFull?: string | null,
): EvidenceDrilldownRow {
  const full = digestFull?.trim() || null;
  return {
    __id: `paper:${id}`,
    surface,
    status,
    trust,
    blockers: blk,
    warnings: wrn,
    at: at || PENDING,
    digestPreview: full ? full.slice(0, 18) : PENDING,
    digestFull: full,
    raw,
  };
}

function viewBlkWrn(v: Record<string, unknown> | null): { blk: number; wrn: number } {
  if (!v) return { blk: 0, wrn: 0 };
  return {
    blk: typeof v.blocker_count === "number" ? (v.blocker_count as number) : arrLen(v.blockers),
    wrn: typeof v.warning_count === "number" ? (v.warning_count as number) : arrLen(v.warnings),
  };
}

export function buildPaperExecutionEvidenceRows(root: Record<string, unknown> | null): EvidenceDrilldownRow[] {
  if (!root) {
    return [
      paperRow("posture", "Execution posture", null, UNKNOWN, UNKNOWN, 0, 0, PENDING),
      paperRow("bundle", "Evidence bundle (latest)", null, UNKNOWN, UNKNOWN, 0, 0, PENDING),
    ];
  }
  const summary = asRecord(root.summary);
  const gen = asString(root.generated_at_utc) ?? PENDING;
  const cap = asString(summary?.paper_submission_capability) ?? UNKNOWN;
  const brokerPolicy = asString(summary?.broker_policy_status) ?? UNKNOWN;
  const execAuth = asString(root.execution_authority) ?? UNKNOWN;
  const promoAuth = asString(root.promotion_authority) ?? UNKNOWN;
  const paperOnly = root.no_live_trading === true && root.no_browser_orders === true;
  const postureStatus = `${cap} · BROKER_${brokerPolicy}${paperOnly ? " · PAPER_ONLY" : ""}${
    /BLOCK/i.test(execAuth) || /BLOCK/i.test(promoAuth) ? " · LIVE_BLOCKED" : ""
  }`;

  const rows: EvidenceDrilldownRow[] = [];

  const postureBlk =
    (typeof summary?.submission_guard_blocker_count === "number" ? summary.submission_guard_blocker_count : 0) +
    (typeof summary?.evidence_bundle_blocker_count === "number" ? summary.evidence_bundle_blocker_count : 0) +
    (typeof summary?.timeline_blocker_count === "number" ? summary.timeline_blocker_count : 0) +
    (typeof summary?.evidence_freshness_blocker_count === "number" ? summary.evidence_freshness_blocker_count : 0);
  const postureWrn =
    (typeof summary?.timeline_warning_count === "number" ? summary.timeline_warning_count : 0) +
    (typeof summary?.position_reconciliation_warning_count === "number" ? summary.position_reconciliation_warning_count : 0);

  rows.push(
    paperRow(
      "posture",
      "Execution posture",
      {
        no_live_trading: root.no_live_trading,
        no_browser_orders: root.no_browser_orders,
        read_plane_only: root.read_plane_only,
        execution_authority: root.execution_authority,
        promotion_authority: root.promotion_authority,
        paper_submission_authority: root.paper_submission_authority,
        mutation_authority: root.mutation_authority,
        summary: summary ?? null,
      },
      postureStatus,
      asString(summary?.latest_evidence_bundle_trust_banner) ?? UNKNOWN,
      postureBlk,
      postureWrn,
      gen,
      asString(summary?.latest_evidence_bundle_sha256),
    ),
  );

  const dry = Array.isArray(root.dry_run_results) && root.dry_run_results[0] != null ? asRecord(root.dry_run_results[0]) : null;
  rows.push(
    paperRow(
      "dry_run",
      "Dry-run evidence",
      dry ?? { hint: "no_dry_run_rows" },
      asString(summary?.selected_intent_dry_run_status) ?? (dry ? asString(dry.status) ?? UNKNOWN : UNKNOWN),
      asString(dry?.trust_banner) ?? UNKNOWN,
      viewBlkWrn(dry).blk,
      viewBlkWrn(dry).wrn,
      asString(summary?.latest_dry_run_artifact_at_utc) ?? asString(dry?.generated_at_utc) ?? gen,
      asString(summary?.latest_dry_run_source_selection_sha256) ?? asString(dry?.artifact_sha256),
    ),
  );

  const bundle = asRecord(root.latest_evidence_bundle);
  const bvw = viewBlkWrn(bundle);
  rows.push(
    paperRow(
      "bundle",
      "Evidence bundle (latest)",
      bundle ?? { empty: true },
      asString(summary?.latest_evidence_bundle_status) ?? asString(bundle?.bundle_status) ?? UNKNOWN,
      asString(summary?.latest_evidence_bundle_trust_banner) ?? asString(bundle?.trust_banner) ?? UNKNOWN,
      typeof summary?.evidence_bundle_blocker_count === "number" ? (summary.evidence_bundle_blocker_count as number) : bvw.blk,
      0,
      asString(summary?.latest_evidence_bundle_at_utc) ?? asString(bundle?.generated_at_utc) ?? gen,
      asString(summary?.latest_evidence_bundle_sha256) ?? asString(bundle?.artifact_sha256),
    ),
  );

  const ver = asRecord(root.latest_evidence_bundle_verification);
  const vw = viewBlkWrn(ver);
  rows.push(
    paperRow(
      "bundle_verify",
      "Bundle verification",
      ver ?? { empty: true },
      asString(summary?.latest_evidence_bundle_verification_status) ?? asString(ver?.verification_status) ?? UNKNOWN,
      asString(summary?.latest_evidence_bundle_verification_trust_banner) ?? asString(ver?.trust_banner) ?? UNKNOWN,
      typeof summary?.evidence_bundle_verification_blocker_count === "number"
        ? (summary.evidence_bundle_verification_blocker_count as number)
        : vw.blk,
      vw.wrn,
      asString(summary?.latest_evidence_bundle_verification_at_utc) ?? asString(ver?.generated_at_utc) ?? gen,
      asString(summary?.latest_evidence_bundle_verification_sha256) ?? asString(ver?.artifact_sha256),
    ),
  );

  const drift = asRecord(root.latest_evidence_bundle_drift);
  const dw = viewBlkWrn(drift);
  rows.push(
    paperRow(
      "bundle_drift",
      "Bundle drift",
      drift ?? { empty: true },
      asString(summary?.latest_evidence_bundle_drift_status) ?? asString(drift?.drift_status) ?? UNKNOWN,
      asString(summary?.latest_evidence_bundle_drift_trust_banner) ?? asString(drift?.trust_banner) ?? UNKNOWN,
      typeof summary?.evidence_bundle_drift_blocker_count === "number" ? (summary.evidence_bundle_drift_blocker_count as number) : dw.blk,
      (typeof summary?.evidence_bundle_drift_new_source_count === "number" ? (summary.evidence_bundle_drift_new_source_count as number) : 0) +
        (typeof summary?.evidence_bundle_drift_removed_source_count === "number"
          ? (summary.evidence_bundle_drift_removed_source_count as number)
          : 0),
      asString(summary?.latest_evidence_bundle_drift_at_utc) ?? asString(drift?.generated_at_utc) ?? gen,
      asString(summary?.latest_evidence_bundle_drift_sha256) ?? asString(drift?.artifact_sha256),
    ),
  );

  const att = asRecord(root.latest_evidence_bundle_attestation);
  const aw = viewBlkWrn(att);
  rows.push(
    paperRow(
      "bundle_attest",
      "Bundle attestation",
      att ?? { empty: true },
      asString(summary?.latest_evidence_bundle_attestation_status) ?? asString(att?.attestation_status) ?? UNKNOWN,
      asString(summary?.latest_evidence_bundle_attestation_trust_banner) ?? asString(att?.trust_banner) ?? UNKNOWN,
      typeof summary?.evidence_bundle_attestation_blocker_count === "number" ? (summary.evidence_bundle_attestation_blocker_count as number) : aw.blk,
      aw.wrn,
      asString(summary?.latest_evidence_bundle_attestation_at_utc) ?? asString(att?.generated_at_utc) ?? gen,
      asString(summary?.latest_evidence_bundle_attestation_sha256) ?? asString(att?.artifact_sha256),
    ),
  );

  const clo = asRecord(root.latest_evidence_bundle_closure);
  const cw = viewBlkWrn(clo);
  rows.push(
    paperRow(
      "bundle_closure",
      "Bundle closure",
      clo ?? { empty: true },
      asString(summary?.latest_evidence_bundle_closure_status) ?? asString(clo?.closure_status) ?? UNKNOWN,
      asString(summary?.latest_evidence_bundle_closure_trust_banner) ?? asString(clo?.trust_banner) ?? UNKNOWN,
      typeof summary?.evidence_bundle_closure_blocker_count === "number" ? (summary.evidence_bundle_closure_blocker_count as number) : cw.blk,
      cw.wrn,
      asString(summary?.latest_evidence_bundle_closure_at_utc) ?? asString(clo?.generated_at_utc) ?? gen,
      asString(summary?.latest_evidence_bundle_closure_sha256) ?? asString(clo?.artifact_sha256),
    ),
  );

  const ret = asRecord(root.latest_evidence_bundle_retention_receipt);
  const rw = viewBlkWrn(ret);
  rows.push(
    paperRow(
      "retention",
      "Retention receipt",
      ret ?? { empty: true },
      asString(ret?.retention_status) ?? asString(ret?.receipt_status) ?? UNKNOWN,
      asString(ret?.trust_banner) ?? UNKNOWN,
      rw.blk,
      rw.wrn,
      asString(ret?.generated_at_utc) ?? gen,
      asString(ret?.artifact_sha256),
    ),
  );

  return rows;
}

export function researchOsAggregateDigest(statusRoot: Record<string, unknown> | null): string | undefined {
  if (!statusRoot) return undefined;
  const demo = asRecord(statusRoot.runtime_demo_manifest);
  const d = asString(demo?.manifest_sha256);
  if (d) return d;
  const closure = asRecord(statusRoot.research_os_closure_latest);
  const latest = pickLatest(closure);
  return asString(latest?.manifest_sha256) ?? undefined;
}

