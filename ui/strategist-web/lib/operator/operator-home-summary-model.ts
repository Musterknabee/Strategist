import { buildResearchBatchForensicsModel } from "@/lib/operator/research-batch-forensics-model";
import { buildStrategyLifecycleModel } from "@/lib/operator/strategy-lifecycle-model";
import { asNumber, asRecord, asString } from "@/lib/operator/payload-utils";

export type OperatorHomeOverallStatus = "OK" | "NEEDS_REVIEW" | "BLOCKED" | "DEGRADED" | "UNKNOWN";
export type PaperResult = "WIN" | "LOSS" | "FLAT" | "UNKNOWN" | "NO_PAPER_DATA";
export type StrategyScoreboardRow = { strategy_id: string; label: string; status: string; paper_result: PaperResult; paper_result_label: string; evidence_status: string; provider_status: string; replay_status: string; blocker_count: number; warning_count: number; graveyard_status: string; duplicate_status: string; last_seen_at_utc: string; digest_prefix: string; next_action: string; detail_target: string; };
export type OperatorHomeSummary = { generated_at_utc: string; overall_status: OperatorHomeOverallStatus; strategy_count: number | null; active_candidate_count: number | null; paper_win_count: number; paper_loss_count: number; paper_unknown_count: number; blocked_count: number; warning_count: number; graveyarded_count: number; duplicate_warning_count: number; replay_verified_count: number; replay_problem_count: number; provider_ok_count: number; provider_pending_key_count: number; stale_data_count: number; next_action: string; next_action_reason: string; top_attention_items: string[]; strategy_rows: StrategyScoreboardRow[]; };

function paperResultFromTracking(p: unknown): { result: PaperResult; label: string } {
  const latest = asRecord(asRecord(p)?.latest);
  const cum = asNumber(asRecord(latest?.scorecard)?.cumulative_paper_return);
  if (!latest) return { result: "NO_PAPER_DATA", label: "No paper result yet" };
  if (cum === undefined) return { result: "UNKNOWN", label: "Paper result unknown" };
  if (cum > 0) return { result: "WIN", label: "Paper win (research-only)" };
  if (cum < 0) return { result: "LOSS", label: "Paper loss (research-only)" };
  return { result: "FLAT", label: "Paper flat (research-only)" };
}
function replayStatus(p: unknown) { const r = asRecord(asRecord(p)?.artifact_replay); return { status: asString(r?.status) ?? "UNKNOWN", mismatch: asNumber(r?.digest_mismatch_count) ?? 0, missing: asNumber(r?.missing_artifact_count) ?? 0 }; }
function pickGeneratedAt(parts: unknown[]) { for (const x of parts) { const ts = asString(asRecord(x)?.generated_at_utc); if (ts) return ts; } return "UNKNOWN"; }

export function buildOperatorHomeSummary(input: { strategyIntakeLatest: unknown; strategyThesisLatest: unknown; strategyThesisGenerationLatest: unknown; strategyMemoryLatest: unknown; strategyGraveyardLatest: unknown; paperTrackingLatest: unknown; backtestForensicsLatest: unknown; strategyBatchLatest: unknown; workboard: unknown; evidenceChain: unknown; providerHealth: unknown; providerSetup: unknown; anyError: boolean; }): OperatorHomeSummary {
  const lifecycle = buildStrategyLifecycleModel({ strategyIntakeLatest: input.strategyIntakeLatest, strategyThesisLatest: input.strategyThesisLatest, strategyThesisGenerationLatest: input.strategyThesisGenerationLatest, strategyMemoryLatest: input.strategyMemoryLatest, strategyGraveyardLatest: input.strategyGraveyardLatest, paperTrackingLatest: input.paperTrackingLatest, backtestForensicsLatest: input.backtestForensicsLatest, strategyBatchLatest: input.strategyBatchLatest, workboard: input.workboard, evidenceChain: input.evidenceChain });
  const forensics = buildResearchBatchForensicsModel({ strategyBatchLatest: input.strategyBatchLatest, strategyBatchesList: null, backtestForensicsLatest: input.backtestForensicsLatest, paperTrackingLatest: input.paperTrackingLatest, strategyGraveyardLatest: input.strategyGraveyardLatest, strategyMemoryLatest: input.strategyMemoryLatest, strategyThesisLatest: input.strategyThesisLatest, shadowBookLatest: null });
  const paperResult = paperResultFromTracking(input.paperTrackingLatest);
  const replaySet = [replayStatus(input.strategyBatchLatest), replayStatus(input.backtestForensicsLatest), replayStatus(input.paperTrackingLatest)];
  const providerEntries = Array.isArray(asRecord(input.providerHealth)?.entries)
    ? (asRecord(input.providerHealth)?.entries as unknown[])
    : [];
  let providerOk = 0;
  let providerPending = 0;
  for (const e of providerEntries) {
    const s = (asString(asRecord(e)?.classified_status) ?? "UNKNOWN").toUpperCase();
    if (s === "OK") providerOk += 1;
    if (s === "PENDING_KEY") providerPending += 1;
  }
  const staleData = asNumber(asRecord(asRecord(input.providerSetup)?.summary)?.stale_count) ?? 0;
  const duplicateWarnings = asNumber(asRecord(asRecord(input.strategyMemoryLatest)?.latest)?.duplicate_variant_count) ?? 0;
  const graveyardedCount = asNumber(asRecord(asRecord(input.strategyGraveyardLatest)?.summary)?.hard_blocked_count) ?? 0;
  const strategyCount = asNumber(asRecord(asRecord(input.workboard)?.stats)?.active_count) ?? null;
  const candidateCount = asNumber(asRecord(asRecord(input.strategyBatchLatest)?.latest)?.candidate_count) ?? strategyCount;
  const replayProblems = replaySet.reduce((n, r) => n + r.mismatch + r.missing, 0);
  const replayVerified = replaySet.filter((r) => r.status === "OK").length;
  const replayProblemCount = replayProblems > 0 ? replayProblems : replaySet.filter((r) => r.status !== "OK" && r.status !== "UNKNOWN").length;
  const blocked = lifecycle.blocker_count + forensics.totals.degraded_count;
  const warnings = lifecycle.warning_count + forensics.totals.requires_review_count;
  const strategyRows: StrategyScoreboardRow[] = [{ strategy_id: lifecycle.strategy_id, label: lifecycle.strategy_id === "UNKNOWN" ? "Unknown strategy" : lifecycle.strategy_id, status: lifecycle.current_stage, paper_result: paperResult.result, paper_result_label: paperResult.label, evidence_status: lifecycle.trust_or_freshness, provider_status: providerPending > 0 ? "Data key missing" : providerOk > 0 ? "Provider OK" : "Provider unknown", replay_status: replayProblemCount > 0 ? "REPLAY_DEGRADED" : replayVerified > 0 ? "REPLAY_OK" : "REPLAY_UNKNOWN", blocker_count: lifecycle.blocker_count, warning_count: lifecycle.warning_count, graveyard_status: graveyardedCount > 0 ? "GRAVEYARDED_PRESENT" : "CLEAR", duplicate_status: duplicateWarnings > 0 ? "DUPLICATE_WARNING" : "NONE", last_seen_at_utc: lifecycle.generated_at_utc, digest_prefix: lifecycle.digest_prefix, next_action: lifecycle.next_review_action, detail_target: "RESEARCH_REVIEW" }];
  const attention: string[] = []; if (blocked > 0) attention.push(`Blocked items: ${blocked}`); if (providerPending > 0) attention.push(`Data key missing for ${providerPending} provider(s)`); if (staleData > 0) attention.push(`Stale provider/data items: ${staleData}`); if (replayProblemCount > 0) attention.push(`Evidence mismatch or missing replay artifacts: ${replayProblemCount}`); if (graveyardedCount > 0) attention.push(`Graveyarded strategies: ${graveyardedCount}`); if (paperResult.result === "NO_PAPER_DATA" || paperResult.result === "UNKNOWN") attention.push("No paper result yet for latest strategy"); if (duplicateWarnings > 0) attention.push(`Duplicate strategy warnings: ${duplicateWarnings}`); if (input.anyError) attention.push("One or more read-plane queries failed; treat unknown fields as pending");
  let overall: OperatorHomeOverallStatus = "OK"; if (input.anyError || replayProblemCount > 0) overall = "DEGRADED"; else if (blocked > 0) overall = "BLOCKED"; else if (warnings > 0 || staleData > 0 || providerPending > 0) overall = "NEEDS_REVIEW"; else if (strategyCount == null) overall = "UNKNOWN";
  const nextAction = lifecycle.next_review_action;
  const nextActionReason = nextAction === "REFRESH_EVIDENCE" ? "Evidence freshness or chain issue is present." : nextAction === "REVIEW_BLOCKERS" ? "Lifecycle blockers are present and must be reviewed first." : nextAction === "CONSIDER_PAPER_TRACKING" ? "Thesis is evaluated but paper tracking linkage is missing." : nextAction === "NO_IMMEDIATE_ACTION" ? "No immediate blocker from read-plane evidence." : "Derived from strategy lifecycle read-plane payloads.";
  const paperWinCount = paperResult.result === "WIN" ? 1 : 0; const paperLossCount = paperResult.result === "LOSS" ? 1 : 0; const paperUnknownCount = paperResult.result === "UNKNOWN" || paperResult.result === "NO_PAPER_DATA" ? 1 : 0;
  return { generated_at_utc: pickGeneratedAt([input.workboard, input.paperTrackingLatest, input.strategyBatchLatest, input.providerHealth]), overall_status: overall, strategy_count: strategyCount, active_candidate_count: candidateCount, paper_win_count: paperWinCount, paper_loss_count: paperLossCount, paper_unknown_count: paperUnknownCount, blocked_count: blocked, warning_count: warnings, graveyarded_count: graveyardedCount, duplicate_warning_count: duplicateWarnings, replay_verified_count: replayVerified, replay_problem_count: replayProblemCount, provider_ok_count: providerOk, provider_pending_key_count: providerPending, stale_data_count: staleData, next_action: nextAction, next_action_reason: nextActionReason, top_attention_items: attention.slice(0, 5), strategy_rows: strategyRows };
}
