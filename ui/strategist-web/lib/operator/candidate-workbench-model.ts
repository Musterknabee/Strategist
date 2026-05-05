import { asNumber, asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import type { OperatorModeId } from "@/lib/operator/operator-modes";

export type CandidateLifecycleState = "ACTIVE" | "WATCHLIST" | "NEEDS_REVIEW" | "BLOCKED" | "GRAVEYARDED" | "UNKNOWN";
export type CandidatePaperResult =
  | "PAPER_WIN"
  | "PAPER_LOSS"
  | "PAPER_FLAT"
  | "NO_PAPER_DATA"
  | "STALE_DATA"
  | "INVALID_RUN"
  | "BLOCKED"
  | "UNKNOWN";
export type CandidateEvidenceStatus = "VERIFIED" | "DEGRADED" | "MISSING" | "DIGEST_MISMATCH" | "UNKNOWN";
export type CandidateReplayStatus = "VERIFIED" | "MISSING" | "DIGEST_MISMATCH" | "NOT_REPLAYABLE" | "UNKNOWN";
export type CandidateProviderStatus = "OK" | "PENDING_KEY" | "STALE" | "UNAVAILABLE" | "UNKNOWN";
export type CandidateDuplicateStatus = "DUPLICATE_WARNING" | "POSSIBLE_VARIANT" | "NO_WARNING" | "UNKNOWN";
export type CandidateGraveyardStatus = "PRIOR_DEATH_REASON" | "GRAVEYARDED" | "NO_MATCH" | "UNKNOWN";
export type CandidateNextAction =
  | "REVIEW_CANDIDATE"
  | "RUN_PAPER_TRACKING"
  | "CHECK_EVIDENCE"
  | "VERIFY_REPLAY"
  | "REVIEW_DUPLICATE_WARNING"
  | "REVIEW_GRAVEYARD_REASON"
  | "ADD_PROVIDER_KEY"
  | "REFRESH_PROVIDER_DATA"
  | "WAIT_FOR_MORE_DATA"
  | "NO_SAFE_ACTION"
  | "UNKNOWN";

export type CandidateWorkbenchRow = {
  row_id: string;
  candidate_id: string;
  strategy_id: string;
  label: string;
  lifecycle_state: CandidateLifecycleState;
  paper_result: CandidatePaperResult;
  evidence_status: CandidateEvidenceStatus;
  replay_status: CandidateReplayStatus;
  provider_status: CandidateProviderStatus;
  duplicate_status: CandidateDuplicateStatus;
  graveyard_status: CandidateGraveyardStatus;
  blocker_count: number;
  warning_count: number;
  digest_prefix: string;
  last_seen_at_utc: string;
  next_action: CandidateNextAction;
  detail_targets: OperatorModeId[];
  raw_refs: string[];
};

export type CandidateWorkbenchSummary = {
  generated_at_utc: string;
  candidate_count: number;
  ready_for_review_count: number;
  needs_review_count: number;
  blocked_count: number;
  no_paper_data_count: number;
  paper_win_count: number;
  paper_loss_count: number;
  duplicate_warning_count: number;
  graveyard_warning_count: number;
  evidence_problem_count: number;
  replay_problem_count: number;
  next_action: CandidateNextAction;
  next_action_reason: string;
  rows: CandidateWorkbenchRow[];
};

function digestPrefix(value: unknown): string {
  const text = asString(value);
  if (!text) return "—";
  return text.length > 12 ? `${text.slice(0, 12)}...` : text;
}

function paperResultFromTracking(
  paperTrackingLatest: unknown,
  strategyId: string,
): { result: CandidatePaperResult; blockerCount: number; warningCount: number; trackingId: string; generatedAt: string } {
  const payload = asRecord(paperTrackingLatest);
  const latest = asRecord(payload?.latest);
  if (!latest) return { result: "NO_PAPER_DATA", blockerCount: 0, warningCount: 0, trackingId: "UNKNOWN", generatedAt: "UNKNOWN" };

  const manifest = asRecord(latest.manifest);
  const candidate = asRecord(manifest?.candidate);
  const trackedStrategyId = asString(candidate?.strategy_id) ?? "UNKNOWN";
  if (strategyId !== "UNKNOWN" && trackedStrategyId !== "UNKNOWN" && trackedStrategyId !== strategyId) {
    return { result: "NO_PAPER_DATA", blockerCount: 0, warningCount: 0, trackingId: "UNKNOWN", generatedAt: "UNKNOWN" };
  }

  const blockers = asStringArray(latest.lifecycle_blockers);
  const warnings = asNumber(asRecord(latest.scorecard)?.warning_count) ?? 0;
  const degraded = asStringArray(payload?.degraded);
  const trackingId = asString(latest.tracking_id) ?? "UNKNOWN";
  const generatedAt = asString(payload?.generated_at_utc) ?? "UNKNOWN";
  if (blockers.length > 0) return { result: "BLOCKED", blockerCount: blockers.length, warningCount: warnings, trackingId, generatedAt };
  if (degraded.some((entry) => entry.includes("UNREADABLE"))) {
    return { result: "INVALID_RUN", blockerCount: 0, warningCount: warnings + degraded.length, trackingId, generatedAt };
  }
  if (degraded.length > 0) return { result: "STALE_DATA", blockerCount: 0, warningCount: warnings + degraded.length, trackingId, generatedAt };

  const scorecard = asRecord(latest.scorecard);
  const cumulative = asNumber(scorecard?.cumulative_paper_return);
  if (cumulative === undefined) return { result: "NO_PAPER_DATA", blockerCount: 0, warningCount: warnings, trackingId, generatedAt };
  if (cumulative > 0) return { result: "PAPER_WIN", blockerCount: 0, warningCount: warnings, trackingId, generatedAt };
  if (cumulative < 0) return { result: "PAPER_LOSS", blockerCount: 0, warningCount: warnings, trackingId, generatedAt };
  return { result: "PAPER_FLAT", blockerCount: 0, warningCount: warnings, trackingId, generatedAt };
}

function providerStatus(providerSetup: unknown, providerHealth: unknown): CandidateProviderStatus {
  const setupSummary = asRecord(asRecord(providerSetup)?.summary);
  const missing = asNumber(setupSummary?.missing_secret_count) ?? 0;
  if (missing > 0) return "PENDING_KEY";
  const healthEntries = asRecord(providerHealth)?.entries;
  if (!Array.isArray(healthEntries) || healthEntries.length === 0) return "UNKNOWN";
  const hasUnavailable = healthEntries.some((entry) => asString(asRecord(entry)?.classified_status) === "AUTH_FAILED");
  if (hasUnavailable) return "UNAVAILABLE";
  const hasStale = healthEntries.some((entry) => asString(asRecord(entry)?.classified_status) === "NOT_CHECKED");
  if (hasStale) return "STALE";
  return "OK";
}

function replayStatus(evidenceChain: unknown): CandidateReplayStatus {
  const payload = asRecord(evidenceChain);
  if (!payload) return "UNKNOWN";
  const degraded = asStringArray(payload.degraded);
  if (degraded.length > 0) return "DIGEST_MISMATCH";
  const summary = asRecord(payload.summary);
  const issues = asNumber(summary?.chain_issue_count_total) ?? 0;
  if (issues > 0) return "DIGEST_MISMATCH";
  const timeline = asRecord(payload.timeline);
  const entries = timeline?.entries;
  if (!Array.isArray(entries) || entries.length === 0) return "MISSING";
  return "VERIFIED";
}

function evidenceStatus(forensicsRow: Record<string, unknown> | null): CandidateEvidenceStatus {
  if (!forensicsRow) return "MISSING";
  const blockers = asStringArray(forensicsRow.blockers);
  if (blockers.length > 0) return "DEGRADED";
  const riskFlags = asStringArray(forensicsRow.risk_flags);
  if (riskFlags.length > 0) return "DEGRADED";
  const artifacts = asRecord(forensicsRow.artifacts);
  const observed = asRecord(artifacts?.observed_sha256);
  if (!observed) return "MISSING";
  return "VERIFIED";
}

function lifecycleState(
  graveyardStatus: CandidateGraveyardStatus,
  paperResult: CandidatePaperResult,
  blockerCount: number,
  warningCount: number,
): CandidateLifecycleState {
  if (graveyardStatus === "GRAVEYARDED") return "GRAVEYARDED";
  if (blockerCount > 0 || paperResult === "BLOCKED" || paperResult === "INVALID_RUN") return "BLOCKED";
  if (warningCount > 0 || paperResult === "NO_PAPER_DATA" || paperResult === "STALE_DATA") return "NEEDS_REVIEW";
  if (paperResult === "PAPER_WIN" || paperResult === "PAPER_LOSS" || paperResult === "PAPER_FLAT") return "ACTIVE";
  return "UNKNOWN";
}

export function buildCandidateWorkbenchModel(input: {
  strategyMemoryLatest: unknown;
  strategyGraveyardLatest: unknown;
  backtestForensicsLatest: unknown;
  paperTrackingLatest: unknown;
  providerSetup: unknown;
  providerHealth: unknown;
  evidenceChain: unknown;
}): CandidateWorkbenchSummary {
  const memory = asRecord(input.strategyMemoryLatest);
  const memoryLatest = asRecord(memory?.latest);
  const records = Array.isArray(memoryLatest?.memory_records) ? memoryLatest.memory_records : [];
  const graveyardEntries = Array.isArray(asRecord(input.strategyGraveyardLatest)?.entries)
    ? (asRecord(input.strategyGraveyardLatest)?.entries as unknown[])
    : [];
  const forensicsRows = Array.isArray(asRecord(input.backtestForensicsLatest)?.strategies)
    ? (asRecord(input.backtestForensicsLatest)?.strategies as unknown[])
    : [];
  const duplicateWarnings = asNumber(memoryLatest?.duplicate_variant_count) ?? 0;
  const provider = providerStatus(input.providerSetup, input.providerHealth);
  const replay = replayStatus(input.evidenceChain);

  const rows: CandidateWorkbenchRow[] = records.map((record, index) => {
    const row = asRecord(record) ?? {};
    const strategyId = asString(row.strategy_id) ?? "UNKNOWN";
    const forensics = forensicsRows.find((entry) => asString(asRecord(entry)?.strategy_id) === strategyId);
    const forensicsRow = asRecord(forensics);
    const graveyard = graveyardEntries.find((entry) => asString(asRecord(entry)?.strategy_id) === strategyId);
    const graveyardRow = asRecord(graveyard);

    const paper = paperResultFromTracking(input.paperTrackingLatest, strategyId);
    const evidence = evidenceStatus(forensicsRow);
    const duplicateStatus: CandidateDuplicateStatus = duplicateWarnings > 0 ? "DUPLICATE_WARNING" : "NO_WARNING";
    const graveyardStatus: CandidateGraveyardStatus = graveyardRow
      ? asString(graveyardRow.status) === "HARD_BLOCKED"
        ? "GRAVEYARDED"
        : "PRIOR_DEATH_REASON"
      : "NO_MATCH";

    const blockers = paper.blockerCount + asStringArray(forensicsRow?.blockers).length + asStringArray(graveyardRow?.hard_blockers).length;
    const warnings = paper.warningCount + asStringArray(forensicsRow?.warnings).length + (graveyardRow ? 1 : 0);
    const lifecycle = lifecycleState(graveyardStatus, paper.result, blockers, warnings);

    const nextAction: CandidateNextAction =
      provider === "PENDING_KEY"
        ? "ADD_PROVIDER_KEY"
        : lifecycle === "BLOCKED"
          ? "REVIEW_CANDIDATE"
          : paper.result === "NO_PAPER_DATA"
            ? "RUN_PAPER_TRACKING"
            : evidence !== "VERIFIED"
              ? "CHECK_EVIDENCE"
              : replay !== "VERIFIED"
                ? "VERIFY_REPLAY"
                : duplicateStatus === "DUPLICATE_WARNING"
                  ? "REVIEW_DUPLICATE_WARNING"
                  : graveyardStatus !== "NO_MATCH"
                    ? "REVIEW_GRAVEYARD_REASON"
                    : "WAIT_FOR_MORE_DATA";

    return {
      row_id: `${strategyId}:${index}`,
      candidate_id: paper.trackingId,
      strategy_id: strategyId,
      label: strategyId,
      lifecycle_state: lifecycle,
      paper_result: paper.result,
      evidence_status: evidence,
      replay_status: replay,
      provider_status: provider,
      duplicate_status: duplicateStatus,
      graveyard_status: graveyardStatus,
      blocker_count: blockers,
      warning_count: warnings,
      digest_prefix: digestPrefix(row.latest_manifest_sha256 ?? forensicsRow?.artifacts),
      last_seen_at_utc: asString(row.updated_at_utc) ?? paper.generatedAt,
      next_action: nextAction,
      detail_targets: ["RESEARCH_REVIEW", "FORENSIC_AUDIT", "CAPITAL_FIREWALL", "FIRST_RUN"],
      raw_refs: ["strategy_memory_latest", "strategy_graveyard_latest", "backtest_forensics_latest", "paper_tracking_latest"],
    };
  });

  const candidateCount = rows.length;
  const blockedCount = rows.filter((row) => row.lifecycle_state === "BLOCKED" || row.lifecycle_state === "GRAVEYARDED").length;
  const needsReviewCount = rows.filter((row) => row.lifecycle_state === "NEEDS_REVIEW").length;
  const readyReviewCount = rows.filter((row) => row.lifecycle_state === "ACTIVE").length;
  const paperWinCount = rows.filter((row) => row.paper_result === "PAPER_WIN").length;
  const paperLossCount = rows.filter((row) => row.paper_result === "PAPER_LOSS").length;
  const noPaperCount = rows.filter((row) => row.paper_result === "NO_PAPER_DATA").length;
  const duplicateCount = rows.filter((row) => row.duplicate_status !== "NO_WARNING").length;
  const graveyardCount = rows.filter((row) => row.graveyard_status !== "NO_MATCH").length;
  const evidenceProblems = rows.filter((row) => row.evidence_status !== "VERIFIED").length;
  const replayProblems = rows.filter((row) => row.replay_status !== "VERIFIED").length;

  const nextAction: CandidateNextAction =
    blockedCount > 0
      ? "REVIEW_CANDIDATE"
      : noPaperCount > 0
        ? "RUN_PAPER_TRACKING"
        : provider === "PENDING_KEY"
          ? "ADD_PROVIDER_KEY"
          : evidenceProblems > 0
            ? "CHECK_EVIDENCE"
            : "WAIT_FOR_MORE_DATA";
  const nextReason =
    blockedCount > 0
      ? "One or more candidates contain explicit blockers."
      : noPaperCount > 0
        ? "Candidates have no explicit paper outcome evidence yet."
        : provider === "PENDING_KEY"
          ? "Provider setup indicates missing keys."
          : evidenceProblems > 0
            ? "Evidence/replay checks are not fully verified."
            : "No urgent unsafe condition detected in read-plane candidate data.";

  return {
    generated_at_utc: asString(memory?.generated_at_utc) ?? asString(asRecord(input.paperTrackingLatest)?.generated_at_utc) ?? "UNKNOWN",
    candidate_count: candidateCount,
    ready_for_review_count: readyReviewCount,
    needs_review_count: needsReviewCount,
    blocked_count: blockedCount,
    no_paper_data_count: noPaperCount,
    paper_win_count: paperWinCount,
    paper_loss_count: paperLossCount,
    duplicate_warning_count: duplicateCount,
    graveyard_warning_count: graveyardCount,
    evidence_problem_count: evidenceProblems,
    replay_problem_count: replayProblems,
    next_action: nextAction,
    next_action_reason: nextReason,
    rows,
  };
}
