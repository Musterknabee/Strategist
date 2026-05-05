/**
 * Read-plane capital / execution firewall view (no live authority, no broker mutation).
 */
import type { UiMutationSafetyStatus } from "@/lib/api/types";
import { asBool, asNumber, asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";

export type ExecutionFirewallSafetyLabel =
  | "PAPER_ONLY"
  | "LIVE_BLOCKED"
  | "NO_ORDER_SUBMITTED"
  | "NO_NETWORK_CALLS"
  | "DRY_RUN_ONLY"
  | "SUBMISSION_EVIDENCE_PRESENT"
  | "POSITION_RECONCILED"
  | "RECONCILIATION_PENDING"
  | "CAPITAL_AUTHORITY_ABSENT"
  | "UNKNOWN";

export type ExecutionFirewallReviewAction =
  | "RUN_PAPER_EXECUTION_DRY_RUN"
  | "REVIEW_PAPER_ONLY_BOUNDARY"
  | "GENERATE_DRY_RUN_EVIDENCE"
  | "VERIFY_SUBMISSION_MATCHES_SELECTION"
  | "REVIEW_POSITION_RECONCILIATION"
  | "REVIEW_BROKER_PROVIDER_SETUP"
  | "REFRESH_EXECUTION_EVIDENCE"
  | "UNKNOWN";

export type ExecutionFirewallModel = {
  firewall_id: string;
  capital_mode: string;
  live_blocked: boolean;
  paper_only: boolean;
  broker_status: string;
  submission_status: string;
  reconciliation_status: string;
  evidence_freshness_status: string;
  authority_status: string;
  blocker_count: number;
  warning_count: number;
  digest_prefix: string;
  digest_full: string | null;
  generated_at_utc: string;
  recommended_review_action: ExecutionFirewallReviewAction;
  safety_labels: ExecutionFirewallSafetyLabel[];
  proof_lines: string[];
  /** Basename or short path only — no env values. */
  safe_artifact_hints: string[];
  raw_sources: Record<string, unknown>;
};

export type ExecutionFirewallInput = {
  paperExecution: Record<string, unknown> | null;
  paperBroker: Record<string, unknown> | null;
  paperTracking: Record<string, unknown> | null;
  providerSetup: Record<string, unknown> | null;
  providerHealth: Record<string, unknown> | null;
  runtimeMutationSafety: UiMutationSafetyStatus | null;
  executionAuthorityHint: string | null;
  queryFailed: boolean;
};

function digestPrefix(v: unknown): string {
  const s = asString(v);
  if (!s) return "—";
  return s.length > 14 ? `${s.slice(0, 12)}…` : s;
}

function safePathHint(path: unknown): string | undefined {
  const p = asString(path);
  if (!p) return undefined;
  const parts = p.replace(/\\/g, "/").split("/");
  const base = parts[parts.length - 1] || p;
  return base.length > 80 ? `${base.slice(0, 77)}…` : base;
}

function execAuthLiveBlocked(auth: string | undefined): boolean {
  const u = (auth || "").toUpperCase();
  return u.includes("BLOCK") || u.includes("NONE") || u.includes("READ");
}

export function buildExecutionFirewallModel(input: ExecutionFirewallInput): ExecutionFirewallModel {
  const pe = input.paperExecution;
  const summary = pe ? asRecord(pe.summary) : null;
  const pb = input.paperBroker;
  const ps = input.providerSetup;
  const ph = input.providerHealth;

  const noLive = asBool(pe?.no_live_trading) === true;
  const noBrowser = asBool(pe?.no_browser_orders) === true;
  const noNet = asBool(pe?.no_network_calls) === true;
  const execAuth = asString(pe?.execution_authority) ?? input.executionAuthorityHint ?? "UNKNOWN";
  const mutAuth = asString(pe?.mutation_authority) ?? "UNKNOWN";
  const paperSub = asString(pe?.paper_submission_authority) ?? "UNKNOWN";

  const submissionCount = asNumber(summary?.submission_receipt_count) ?? 0;
  const dryCount = asNumber(summary?.dry_run_artifact_count) ?? 0;
  const lastReceipt = Array.isArray(pe?.submission_receipts) && pe.submission_receipts.length > 0 ? asRecord(pe.submission_receipts[0]) : null;
  const recon = pe ? asRecord(pe.position_reconciliation) : null;
  const dryFirst = Array.isArray(pe?.dry_run_results) && pe.dry_run_results[0] != null ? asRecord(pe.dry_run_results[0]) : null;
  const selectedIntent = pe ? asRecord(pe.selected_intent) : null;

  const brokerPolicy = asString(summary?.broker_policy_status) ?? asString(pb?.policy_status) ?? "UNKNOWN";
  const brokerBlockers = asStringArray(pb?.blockers).length + asStringArray(pb?.warnings).filter((w) => w.toUpperCase().includes("BLOCK")).length;
  const setupSummary = asRecord(ps?.summary);
  const setupBlocked = asNumber(setupSummary?.blocked_count) ?? 0;

  const fresh = asString(summary?.evidence_freshness_status) ?? asString(summary?.latest_submission_evidence_freshness_status) ?? "UNKNOWN";
  const guard = asString(lastReceipt?.guard_status) ?? asString(summary?.latest_submission_guard_status) ?? "UNKNOWN";
  const submissionStatus =
    submissionCount > 0
      ? `${submissionCount}_RECEIPTS · guard=${guard} · fresh=${fresh}`
      : "NO_SUBMISSION_RECEIPTS";

  const reconStatus = asString(recon?.status) ?? asString(summary?.position_reconciliation_status) ?? "UNKNOWN";

  const intentLiveBlocked = asBool(selectedIntent?.live_trading_blocked) === true;
  const liveBlocked = noLive || execAuthLiveBlocked(execAuth) || intentLiveBlocked;
  const paperOnly = noLive && noBrowser;

  const safetyLabels: ExecutionFirewallSafetyLabel[] = [];
  if (!pe) safetyLabels.push("UNKNOWN");
  if (paperOnly) safetyLabels.push("PAPER_ONLY");
  if (liveBlocked) safetyLabels.push("LIVE_BLOCKED");
  if (noNet) safetyLabels.push("NO_NETWORK_CALLS");
  if (submissionCount === 0) safetyLabels.push("NO_ORDER_SUBMITTED");
  else safetyLabels.push("SUBMISSION_EVIDENCE_PRESENT");
  if (dryCount > 0 && submissionCount === 0) safetyLabels.push("DRY_RUN_ONLY");
  const ru = reconStatus.toUpperCase();
  if (ru.includes("RECONCILED") && !ru.includes("PENDING")) safetyLabels.push("POSITION_RECONCILED");
  else if (
    (recon && !ru.includes("RECONCILED")) ||
    (asNumber(summary?.position_reconciliation_blocker_count) ?? 0) > 0 ||
    (submissionCount > 0 && ru === "UNKNOWN")
  ) {
    safetyLabels.push("RECONCILIATION_PENDING");
  }
  if (asString(pe?.execution_authority)?.toUpperCase().includes("NONE") || mutAuth.toUpperCase().includes("NONE")) {
    safetyLabels.push("CAPITAL_AUTHORITY_ABSENT");
  }
  if (!safetyLabels.length) safetyLabels.push("UNKNOWN");

  const blockers =
    (typeof summary?.submission_guard_blocker_count === "number" ? (summary.submission_guard_blocker_count as number) : 0) +
    (typeof summary?.evidence_bundle_blocker_count === "number" ? (summary.evidence_bundle_blocker_count as number) : 0) +
    (typeof summary?.timeline_blocker_count === "number" ? (summary.timeline_blocker_count as number) : 0) +
    (typeof summary?.evidence_freshness_blocker_count === "number" ? (summary.evidence_freshness_blocker_count as number) : 0) +
    (typeof summary?.position_reconciliation_blocker_count === "number" ? (summary.position_reconciliation_blocker_count as number) : 0) +
    asStringArray(pb?.blockers).length +
    (recon ? asStringArray(recon.blockers).length : 0) +
    (lastReceipt ? asStringArray(lastReceipt.blockers).length : 0);

  const warnings =
    (typeof summary?.timeline_warning_count === "number" ? (summary.timeline_warning_count as number) : 0) +
    (typeof summary?.position_reconciliation_warning_count === "number" ? (summary.position_reconciliation_warning_count as number) : 0) +
    asStringArray(pb?.warnings).length +
    (recon ? asStringArray(recon.warnings).length : 0) +
    (lastReceipt ? asStringArray(lastReceipt.warnings).length : 0);

  const digestFull =
    asString(summary?.latest_evidence_bundle_sha256) ??
    asString(lastReceipt?.artifact_sha256) ??
    asString(dryFirst?.artifact_sha256) ??
    null;
  const digest = digestFull ?? undefined;

  const proofLines: string[] = [];
  proofLines.push(`execution_authority=${execAuth}`);
  proofLines.push(`paper_submission_authority=${paperSub}`);
  proofLines.push(`mutation_authority=${mutAuth}`);
  proofLines.push(`broker_policy=${brokerPolicy}`);
  if (lastReceipt) {
    proofLines.push(`broker_order_id=${asString(lastReceipt.broker_order_id) ?? "—"}`);
    proofLines.push(`submission_intent_matches_selection=${String(lastReceipt.submission_intent_matches_selection ?? "UNKNOWN")}`);
    proofLines.push(`linked_dry_run_ok=${String(lastReceipt.linked_dry_run_ok ?? "UNKNOWN")}`);
  }
  if (recon) {
    proofLines.push(`observed_position_qty=${asNumber(recon.observed_position_qty) ?? "UNKNOWN"}`);
    proofLines.push(`filled_qty=${asNumber(recon.filled_qty) ?? "UNKNOWN"}`);
  }
  if (fresh) proofLines.push(`evidence_freshness_status=${fresh}`);

  const safeHints: string[] = [];
  const pushHint = (p: unknown) => {
    const h = safePathHint(p);
    if (h) safeHints.push(h);
  };
  pushHint(lastReceipt?.artifact_path);
  pushHint(dryFirst?.artifact_path);
  pushHint(selectedIntent?.source_artifact_path);
  pushHint(recon?.account_position_snapshot_path);

  let action: ExecutionFirewallReviewAction = "UNKNOWN";
  if (!pe) {
    action = "RUN_PAPER_EXECUTION_DRY_RUN";
  } else if (asStringArray(pb?.blockers).length > 0 || brokerPolicy.toUpperCase().includes("BLOCK") || setupBlocked > 0) {
    action = "REVIEW_BROKER_PROVIDER_SETUP";
  } else if (fresh.toUpperCase().includes("STALE") || fresh.toUpperCase().includes("EXPIRED")) {
    action = "REFRESH_EXECUTION_EVIDENCE";
  } else if (paperOnly && noLive) {
    action = "REVIEW_PAPER_ONLY_BOUNDARY";
  } else if (dryCount === 0) {
    action = "GENERATE_DRY_RUN_EVIDENCE";
  } else if (submissionCount > 0 && (reconStatus === "UNKNOWN" || (!reconStatus.toUpperCase().includes("RECONCILED") && reconStatus !== "NOT_APPLICABLE"))) {
    action = "REVIEW_POSITION_RECONCILIATION";
  } else if (lastReceipt && asBool(lastReceipt.submission_intent_matches_selection) === false) {
    action = "VERIFY_SUBMISSION_MATCHES_SELECTION";
  } else if (submissionCount > 0) {
    action = "VERIFY_SUBMISSION_MATCHES_SELECTION";
  } else if (input.queryFailed) {
    action = "RUN_PAPER_EXECUTION_DRY_RUN";
  } else if (asBool(summary?.selected_intent_dry_run_match) === false) {
    action = "GENERATE_DRY_RUN_EVIDENCE";
  }

  const capitalMode = paperOnly ? "PAPER_ONLY" : noLive ? "LIVE_BLOCKED_READ_PLANE" : "UNKNOWN";

  const authorityStatus = [execAuth, paperSub, mutAuth].join(" · ");

  return {
    firewall_id: `firewall:${asString(summary?.latest_tracking_id) ?? asString(pe?.scan_root) ?? "none"}`,
    capital_mode: capitalMode,
    live_blocked: liveBlocked,
    paper_only: paperOnly,
    broker_status: brokerPolicy,
    submission_status: submissionStatus,
    reconciliation_status: reconStatus,
    evidence_freshness_status: fresh,
    authority_status: authorityStatus,
    blocker_count: blockers + brokerBlockers,
    warning_count: warnings,
    digest_prefix: digestPrefix(digest),
    digest_full: digestFull,
    generated_at_utc: asString(pe?.generated_at_utc) ?? asString(pb?.generated_at_utc) ?? "UNKNOWN",
    recommended_review_action: action,
    safety_labels: safetyLabels.length ? safetyLabels : ["UNKNOWN"],
    proof_lines: proofLines,
    safe_artifact_hints: safeHints.slice(0, 8),
    raw_sources: {
      paper_execution: pe ?? {},
      paper_broker: pb ?? {},
      paper_tracking: input.paperTracking ?? {},
      provider_setup: ps ?? {},
      provider_health: ph ?? {},
      runtime_mutation_safety: input.runtimeMutationSafety ?? {},
    },
  };
}

/** For tests: recommended action must never imply live order execution. */
export function reviewActionIsReadPlaneSafe(action: ExecutionFirewallReviewAction): boolean {
  const forbidden = /execute\s*live|live\s*order|submit\s*live/i;
  return !forbidden.test(action);
}
