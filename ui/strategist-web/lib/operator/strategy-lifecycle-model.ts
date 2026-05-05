import type { UiWorkboardPayload } from "@/lib/api/types";
import { deriveWorkboardDegradedReason } from "@/lib/api/types";
import { asBool, asNumber, asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";

export type StrategyLifecycleStage =
  | "INTAKE_PENDING"
  | "INTAKE_ACCEPTED"
  | "THESIS_GENERATED"
  | "THESIS_EVALUATED"
  | "PAPER_TRACKING_LINKED"
  | "BACKTEST_FORENSICS_LINKED"
  | "MEMORY_UPDATED"
  | "GRAVEYARDED"
  | "DEGRADED"
  | "UNKNOWN";

export type StrategyLifecycleReviewAction =
  | "SUBMIT_STRATEGY_IDEA"
  | "GENERATE_THESIS"
  | "EVALUATE_THESIS"
  | "REVIEW_BLOCKERS"
  | "CONSIDER_PAPER_TRACKING"
  | "REVIEW_DEATH_REASON"
  | "REFRESH_EVIDENCE"
  | "NO_IMMEDIATE_ACTION";

export type StrategyLifecycleRow = {
  __id: string;
  section: string;
  run_or_tracking_id: string;
  stage: StrategyLifecycleStage;
  status: string;
  review_status: "REQUIRES_REVIEW" | "DEGRADED" | "PENDING" | "OK";
  trust: string;
  blocker_count: number;
  warning_count: number;
  digest_prefix: string;
  /** Full hash for operator digest copy when present in read-plane payload. */
  digest_full: string | null;
  generated_at_utc: string;
  review_target: string;
  raw: Record<string, unknown>;
};

export type StrategyLifecycleModel = {
  lifecycle_id: string;
  strategy_id: string;
  thesis_id: string;
  intake_id: string;
  tracking_id: string;
  run_id: string;
  current_stage: StrategyLifecycleStage;
  status: string;
  trust_or_freshness: string;
  blocker_count: number;
  warning_count: number;
  digest_prefix: string;
  generated_at_utc: string;
  next_review_action: StrategyLifecycleReviewAction;
  rows: StrategyLifecycleRow[];
};

function digestPrefix(input: unknown): string {
  const value = asString(input);
  if (!value) return "—";
  return value.length > 12 ? `${value.slice(0, 12)}...` : value;
}

function digestFull(input: unknown): string | null {
  const value = asString(input);
  return value && value.length >= 16 ? value : null;
}

function inferReviewStatus(opts: {
  degraded: string[];
  blockerCount: number;
  warningCount: number;
  trust: string;
  status: string;
}): StrategyLifecycleRow["review_status"] {
  if (opts.blockerCount > 0 || opts.degraded.length > 0) return "DEGRADED";
  const statusUpper = opts.status.toUpperCase();
  const trustUpper = opts.trust.toUpperCase();
  if (
    statusUpper.includes("BLOCK") ||
    statusUpper.includes("FAIL") ||
    statusUpper.includes("FALSIFIED") ||
    statusUpper.includes("STALE") ||
    statusUpper.includes("UNTRUST")
  ) {
    return "REQUIRES_REVIEW";
  }
  if (
    statusUpper === "UNKNOWN" ||
    statusUpper === "PENDING" ||
    statusUpper === "NOT_PRESENT" ||
    statusUpper === "NOT_CHECKED"
  ) {
    return "PENDING";
  }
  if (trustUpper.includes("RESTRICTED") || trustUpper.includes("UNTRUST")) return "REQUIRES_REVIEW";
  return "OK";
}

function evidenceChainStale(evidenceChain: unknown): boolean {
  const chain = asRecord(evidenceChain);
  const degraded = asStringArray(chain?.degraded);
  if (degraded.length > 0) return true;
  const summary = asRecord(chain?.summary);
  const issues = asNumber(summary?.chain_issue_count_total) ?? 0;
  if (issues > 0) return true;
  const dlOk = asBool(summary?.decision_ledger_chain_ok);
  const oaOk = asBool(summary?.operator_action_chain_ok);
  if (dlOk === false || oaOk === false) return true;
  return false;
}

function workboardStale(workboard: unknown): boolean {
  const body = asRecord(workboard);
  if (!body) return false;
  const payload = body as unknown as UiWorkboardPayload;
  return deriveWorkboardDegradedReason(payload) != null;
}

export function resolveAnchorIds(input: {
  strategyThesisLatest: unknown;
  strategyThesisGenerationLatest: unknown;
  paperTrackingLatest: unknown;
  strategyBatchLatest: unknown;
  strategyIntakeLatest: unknown;
}): { strategyId: string; thesisId: string; intakeId: string; trackingId: string; runId: string } {
  const thesisPayload = asRecord(input.strategyThesisLatest);
  const evalBody = asRecord(thesisPayload?.latest);
  let thesisId = asString(evalBody?.thesis_id) ?? "";
  let strategyId = asString(evalBody?.strategy_id) ?? "";

  const genPayload = asRecord(input.strategyThesisGenerationLatest);
  const genReport = asRecord(genPayload?.latest_generation);
  const theses = genReport?.generated_theses;
  if (Array.isArray(theses)) {
    for (const t of theses) {
      const tr = asRecord(t);
      if (!strategyId) strategyId = asString(tr?.strategy_id) ?? "";
      if (!thesisId) thesisId = asString(tr?.thesis_id) ?? "";
      if (strategyId && thesisId) break;
    }
  }

  const paper = asRecord(input.paperTrackingLatest);
  const paperLatest = asRecord(paper?.latest);
  const manifest = asRecord(paperLatest?.manifest);
  const cand = asRecord(manifest?.candidate);
  if (!strategyId) strategyId = asString(cand?.strategy_id) ?? "";
  const trackingId = asString(paperLatest?.tracking_id) ?? "";

  const batch = asRecord(input.strategyBatchLatest);
  const batchInner = asRecord(batch?.latest);
  const runId = asString(batchInner?.run_id) ?? "";
  if (!strategyId) strategyId = asString(batchInner?.top_candidate) ?? "";

  const intake = asRecord(input.strategyIntakeLatest);
  const intakeLatest = asRecord(intake?.latest);
  const entries = intakeLatest?.entries;
  let intakeId = "";
  if (Array.isArray(entries) && entries.length > 0) {
    const last = asRecord(entries[entries.length - 1]);
    intakeId = asString(last?.intake_id) ?? "";
    if (!strategyId) strategyId = asString(last?.strategy_name) ?? "";
  }

  return {
    strategyId: strategyId || "UNKNOWN",
    thesisId: thesisId || "UNKNOWN",
    intakeId: intakeId || "UNKNOWN",
    trackingId: trackingId || "UNKNOWN",
    runId: runId || "UNKNOWN",
  };
}

function isGraveyardedForStrategy(strategyGraveyardLatest: unknown, strategyId: string): {
  graveyarded: boolean;
  deathHint: string;
} {
  if (!strategyId || strategyId === "UNKNOWN") return { graveyarded: false, deathHint: "" };
  const gy = asRecord(strategyGraveyardLatest);
  const rawEntries = gy?.entries;
  if (!Array.isArray(rawEntries)) return { graveyarded: false, deathHint: "" };
  for (const e of rawEntries) {
    const row = asRecord(e);
    if (asString(row?.strategy_id) === strategyId) {
      const reasons = asStringArray(row?.failure_reasons);
      const kill = asString(row?.kill_reason);
      const hint = [kill, ...reasons].filter(Boolean).join(" · ").slice(0, 240);
      return { graveyarded: true, deathHint: hint || "GRAVEYARD_ENTRY_PRESENT" };
    }
  }
  return { graveyarded: false, deathHint: "" };
}

function memoryHasStrategy(strategyMemoryLatest: unknown, strategyId: string): boolean {
  if (!strategyId || strategyId === "UNKNOWN") return false;
  const mem = asRecord(strategyMemoryLatest);
  const latest = asRecord(mem?.latest);
  const records = latest?.memory_records;
  if (!Array.isArray(records)) return false;
  return records.some((r) => asString(asRecord(r)?.strategy_id) === strategyId);
}

export function buildStrategyLifecycleModel(input: {
  strategyIntakeLatest: unknown;
  strategyThesisLatest: unknown;
  strategyThesisGenerationLatest: unknown;
  strategyMemoryLatest: unknown;
  strategyGraveyardLatest: unknown;
  paperTrackingLatest: unknown;
  backtestForensicsLatest: unknown;
  strategyBatchLatest: unknown;
  workboard: unknown;
  evidenceChain: unknown;
}): StrategyLifecycleModel {
  const anchor = resolveAnchorIds({
    strategyThesisLatest: input.strategyThesisLatest,
    strategyThesisGenerationLatest: input.strategyThesisGenerationLatest,
    paperTrackingLatest: input.paperTrackingLatest,
    strategyBatchLatest: input.strategyBatchLatest,
    strategyIntakeLatest: input.strategyIntakeLatest,
  });

  const { graveyarded, deathHint } = isGraveyardedForStrategy(input.strategyGraveyardLatest, anchor.strategyId);
  const memoryLinked = memoryHasStrategy(input.strategyMemoryLatest, anchor.strategyId);

  const rows: StrategyLifecycleRow[] = [];

  const intake = asRecord(input.strategyIntakeLatest);
  const intakeLatest = asRecord(intake?.latest);
  const intakeDegraded = asStringArray(intake?.degraded);
  const intakeCount = asNumber(intakeLatest?.intake_count) ?? 0;
  const intakeEntries = Array.isArray(intakeLatest?.entries) ? intakeLatest.entries : [];
  const lastIntake = intakeEntries.length > 0 ? asRecord(intakeEntries[intakeEntries.length - 1]) : null;
  const readiness = asString(lastIntake?.readiness_state) ?? "";
  let intakeStage: StrategyLifecycleStage = "UNKNOWN";
  if (intakeDegraded.length > 0) intakeStage = "DEGRADED";
  else if (intakeCount === 0 || intakeEntries.length === 0) intakeStage = "INTAKE_PENDING";
  else if (readiness === "RESEARCH_INTAKE_RECORDED") intakeStage = "INTAKE_ACCEPTED";
  else if (readiness === "RESEARCH_INTAKE_BLOCKED") intakeStage = "INTAKE_PENDING";
  else intakeStage = "INTAKE_PENDING";
  const intakeBlockers = readiness === "RESEARCH_INTAKE_BLOCKED" ? 1 : 0;
  rows.push({
    __id: "lifecycle-intake",
    section: "Latest intake",
    run_or_tracking_id: asString(lastIntake?.intake_id) ?? asString(lastIntake?.proposal_id) ?? "UNKNOWN",
    stage: intakeStage,
    status: readiness || (intakeCount > 0 ? "INDEX_PRESENT" : "NO_ENTRIES"),
    trust: asString(intake?.read_plane_only) === "true" ? "READ_PLANE" : "UNKNOWN",
    blocker_count: intakeBlockers,
    warning_count: intakeDegraded.length,
    digest_prefix: digestPrefix(lastIntake?.artifact_sha256 ?? intake?.index_path),
    digest_full: digestFull(lastIntake?.artifact_sha256),
    generated_at_utc: asString(lastIntake?.created_at_utc) ?? asString(intake?.generated_at_utc) ?? "UNKNOWN",
    review_target: "verify intake readiness and artifact hash",
    raw: intake ?? {},
    review_status: inferReviewStatus({
      degraded: intakeDegraded,
      blockerCount: intakeBlockers,
      warningCount: intakeDegraded.length,
      trust: "READ_PLANE",
      status: readiness || String(intakeCount),
    }),
  });

  const genPayload = asRecord(input.strategyThesisGenerationLatest);
  const genReport = asRecord(genPayload?.latest_generation);
  const genDegraded = asStringArray(genPayload?.degraded);
  let genStage: StrategyLifecycleStage = "UNKNOWN";
  if (genDegraded.some((c) => c.includes("NO_THESIS_GENERATION"))) genStage = "UNKNOWN";
  else if (genDegraded.length > 0) genStage = "DEGRADED";
  else if (genReport) genStage = "THESIS_GENERATED";
  const genWarnings = asStringArray(genReport?.warnings).length;
  rows.push({
    __id: "lifecycle-thesis-gen",
    section: "Thesis generation",
    run_or_tracking_id: asString(genReport?.run_id) ?? asString(genReport?.batch_id) ?? "UNKNOWN",
    stage: genStage,
    status: genReport ? `generated_count=${asNumber(genReport?.generated_count) ?? 0}` : "NO_REPORT",
    trust: "READ_PLANE",
    blocker_count: 0,
    warning_count: genWarnings + genDegraded.length,
    digest_prefix: digestPrefix(genReport?.report_sha256 ?? genPayload?.latest_path),
    digest_full: digestFull(genReport?.report_sha256),
    generated_at_utc: asString(genReport?.generated_at_utc) ?? asString(genPayload?.generated_at_utc) ?? "UNKNOWN",
    review_target: "open thesis_generation_report.json lineage",
    raw: genPayload ?? {},
    review_status: inferReviewStatus({
      degraded: genDegraded,
      blockerCount: 0,
      warningCount: genWarnings,
      trust: "READ_PLANE",
      status: genStage,
    }),
  });

  const thesisPayload = asRecord(input.strategyThesisLatest);
  const evalBody = asRecord(thesisPayload?.latest);
  const thesisDegraded = asStringArray(thesisPayload?.degraded);
  let evalStage: StrategyLifecycleStage = "UNKNOWN";
  if (thesisDegraded.some((c) => c.includes("NO_THESIS_EVALUATION"))) evalStage = "UNKNOWN";
  else if (thesisDegraded.some((c) => c.includes("UNREADABLE"))) evalStage = "DEGRADED";
  else if (thesisDegraded.length > 0) evalStage = "DEGRADED";
  else if (evalBody) evalStage = "THESIS_EVALUATED";
  const support = asString(evalBody?.support_status) ?? "UNKNOWN";
  const contradictions = Array.isArray(evalBody?.contradictions) ? evalBody.contradictions.length : 0;
  const kills = Array.isArray(evalBody?.triggered_kill_criteria) ? evalBody.triggered_kill_criteria.length : 0;
  const evalBlockers = support === "FALSIFIED" || kills > 0 ? 1 : 0;
  rows.push({
    __id: "lifecycle-thesis-eval",
    section: "Thesis evaluation",
    run_or_tracking_id: asString(evalBody?.strategy_id) ?? anchor.strategyId,
    stage: evalStage,
    status: evalBody ? support : "NO_EVALUATION_FILE",
    trust: "READ_PLANE",
    blocker_count: evalBlockers,
    warning_count: contradictions + thesisDegraded.length,
    digest_prefix: digestPrefix(evalBody?.evaluation_sha256 ?? thesisPayload?.latest_path),
    digest_full: digestFull(evalBody?.evaluation_sha256),
    generated_at_utc: asString(evalBody?.evaluated_at_utc) ?? asString(thesisPayload?.generated_at_utc) ?? "UNKNOWN",
    review_target: "read support_status, contradictions, kill criteria",
    raw: thesisPayload ?? {},
    review_status: inferReviewStatus({
      degraded: thesisDegraded,
      blockerCount: evalBlockers,
      warningCount: contradictions,
      trust: "READ_PLANE",
      status: support,
    }),
  });

  let memStage: StrategyLifecycleStage = "UNKNOWN";
  const mem = asRecord(input.strategyMemoryLatest);
  const memLatest = asRecord(mem?.latest);
  const memDegraded = asStringArray(mem?.degraded);
  if (memDegraded.length > 0) memStage = "DEGRADED";
  else if (memoryLinked) memStage = "MEMORY_UPDATED";
  else if (memLatest && anchor.strategyId !== "UNKNOWN") memStage = "UNKNOWN";
  const dup = asNumber(memLatest?.duplicate_variant_count) ?? 0;
  const killed = asNumber(memLatest?.killed_count) ?? 0;
  rows.push({
    __id: "lifecycle-memory",
    section: "Strategy memory",
    run_or_tracking_id: anchor.strategyId,
    stage: memStage,
    status: memLatest ? "INDEX_PRESENT" : "PENDING",
    trust: asString(memLatest?.index_sha256) ? "INDEX_HASHED" : "UNKNOWN",
    blocker_count: 0,
    warning_count: dup + killed + memDegraded.length,
    digest_prefix: digestPrefix(memLatest?.index_sha256 ?? mem?.index_path),
    digest_full: digestFull(memLatest?.index_sha256),
    generated_at_utc: asString(mem?.generated_at_utc) ?? "UNKNOWN",
    review_target: "confirm memory record for anchored strategy_id",
    raw: mem ?? {},
    review_status: inferReviewStatus({
      degraded: memDegraded,
      blockerCount: 0,
      warningCount: dup + killed,
      trust: "INDEX",
      status: memStage,
    }),
  });

  const paper = asRecord(input.paperTrackingLatest);
  const paperLatest = asRecord(paper?.latest);
  const paperDegraded = asStringArray(paper?.degraded);
  const paperManifest = asRecord(paperLatest?.manifest);
  const candSid = asString(asRecord(paperManifest?.candidate)?.strategy_id);
  let paperStage: StrategyLifecycleStage = "UNKNOWN";
  if (paperDegraded.length > 0) paperStage = "DEGRADED";
  else if (paperLatest?.tracking_id && candSid && anchor.strategyId !== "UNKNOWN" && candSid === anchor.strategyId) {
    paperStage = "PAPER_TRACKING_LINKED";
  } else if (paperLatest?.tracking_id && (!candSid || anchor.strategyId === "UNKNOWN")) {
    paperStage = "PAPER_TRACKING_LINKED";
  } else if (paperLatest?.tracking_id) paperStage = "UNKNOWN";
  const paperBlockers = asStringArray(paperLatest?.lifecycle_blockers).length;
  const paperWarnings = asNumber(asRecord(paperLatest?.scorecard)?.warning_count) ?? 0;
  rows.push({
    __id: "lifecycle-paper",
    section: "Paper tracking",
    run_or_tracking_id: asString(paperLatest?.tracking_id) ?? "UNKNOWN",
    stage: paperStage,
    status: asString(paperLatest?.lifecycle_state) ?? "UNKNOWN",
    trust: asString(paperManifest?.trust_banner) ?? "UNKNOWN",
    blocker_count: paperBlockers,
    warning_count: paperWarnings + paperDegraded.length,
    digest_prefix: digestPrefix(paperManifest?.manifest_sha256 ?? paper?.manifest_path),
    digest_full: digestFull(paperManifest?.manifest_sha256),
    generated_at_utc: asString(paper?.generated_at_utc) ?? "UNKNOWN",
    review_target: "link paper manifest candidate.strategy_id to lifecycle anchor",
    raw: paper ?? {},
    review_status: inferReviewStatus({
      degraded: paperDegraded,
      blockerCount: paperBlockers,
      warningCount: paperWarnings,
      trust: asString(paperManifest?.trust_banner) ?? "UNKNOWN",
      status: asString(paperLatest?.lifecycle_state) ?? "UNKNOWN",
    }),
  });

  const batch = asRecord(input.strategyBatchLatest);
  const batchInner = asRecord(batch?.latest);
  const batchDegraded = asStringArray(batch?.degraded);
  const forensics = asRecord(input.backtestForensicsLatest);
  const forensicsSummary = asRecord(forensics?.summary);
  const forensicsDegraded = asStringArray(forensics?.degraded);
  const batchPresentRaw = forensicsSummary?.batch_present;
  const batchPresent = !(
    batchPresentRaw === false || asString(batchPresentRaw) === "false"
  );
  let bfStage: StrategyLifecycleStage = "UNKNOWN";
  if (batchDegraded.length > 0 || forensicsDegraded.length > 0) bfStage = "DEGRADED";
  else if (batchInner && batchPresent) bfStage = "BACKTEST_FORENSICS_LINKED";
  else if (batchInner || batchPresent) bfStage = "UNKNOWN";
  const fcBlocked = asNumber(forensicsSummary?.blocked_count) ?? 0;
  const fcNeeds = asNumber(forensicsSummary?.needs_evidence_count) ?? 0;
  rows.push({
    __id: "lifecycle-batch-forensics",
    section: "Batch / backtest forensics",
    run_or_tracking_id: asString(batchInner?.run_id) ?? asString(asRecord(forensics?.batch)?.run_id) ?? "UNKNOWN",
    stage: bfStage,
    status: batchInner ? (asBool(batchInner?.ok) === false ? "BATCH_REVIEW" : "OK") : "PENDING",
    trust: "READ_PLANE",
    blocker_count: fcBlocked + (asNumber(batchInner?.blocked_count) ?? 0),
    warning_count: fcNeeds + (asNumber(batchInner?.failed_count) ?? 0) + batchDegraded.length + forensicsDegraded.length,
    digest_prefix: digestPrefix(forensics?.summary_path ?? batchInner?.batch_sha256),
    digest_full: digestFull(batchInner?.batch_sha256),
    generated_at_utc: asString(forensics?.generated_at_utc) ?? asString(batch?.generated_at_utc) ?? "UNKNOWN",
    review_target: "trace run_id across batch summary and forensics",
    raw: { strategy_batch_latest: batch ?? {}, backtest_forensics_latest: forensics ?? {} },
    review_status: inferReviewStatus({
      degraded: [...batchDegraded, ...forensicsDegraded],
      blockerCount: fcBlocked,
      warningCount: fcNeeds,
      trust: "READ_PLANE",
      status: bfStage,
    }),
  });

  let gyStage: StrategyLifecycleStage = graveyarded ? "GRAVEYARDED" : "UNKNOWN";
  const gy = asRecord(input.strategyGraveyardLatest);
  const gySummary = asRecord(gy?.summary);
  const gyDegraded = asStringArray(gy?.degraded);
  if (!graveyarded && gyDegraded.length > 0) gyStage = "DEGRADED";
  rows.push({
    __id: "lifecycle-graveyard",
    section: "Graveyard",
    run_or_tracking_id: anchor.strategyId,
    stage: gyStage,
    status:
      graveyarded
        ? "ENTRY_FOR_ANCHOR"
        : gySummary
          ? `entries=${asNumber(gySummary?.entry_count) ?? 0}`
          : "NO_MATCH",
    trust: "READ_PLANE",
    blocker_count: asNumber(gySummary?.hard_blocked_count) ?? 0,
    warning_count: (asNumber(gySummary?.operator_review_count) ?? 0) + gyDegraded.length,
    digest_prefix: digestPrefix(gy?.index_path),
    digest_full: null,
    generated_at_utc: asString(gy?.generated_at_utc) ?? "UNKNOWN",
    review_target: deathHint || "review graveyard failure_reasons for anchored strategy",
    raw: gy ?? {},
    review_status: inferReviewStatus({
      degraded: gyDegraded,
      blockerCount: graveyarded ? 1 : 0,
      warningCount: asNumber(gySummary?.operator_review_count) ?? 0,
      trust: "READ_PLANE",
      status: gyStage,
    }),
  });

  const totalBlockers = rows.reduce((a, r) => a + r.blocker_count, 0);
  const totalWarnings = rows.reduce((a, r) => a + r.warning_count, 0);

  let currentStage: StrategyLifecycleStage = "UNKNOWN";
  if (graveyarded) currentStage = "GRAVEYARDED";
  else if (rows.some((r) => r.stage === "DEGRADED" || r.review_status === "DEGRADED")) currentStage = "DEGRADED";
  else if (evalStage === "THESIS_EVALUATED" && paperStage === "PAPER_TRACKING_LINKED" && bfStage === "BACKTEST_FORENSICS_LINKED")
    currentStage = "PAPER_TRACKING_LINKED";
  else if (evalStage === "THESIS_EVALUATED") currentStage = "THESIS_EVALUATED";
  else if (genStage === "THESIS_GENERATED") currentStage = "THESIS_GENERATED";
  else if (intakeStage === "INTAKE_ACCEPTED") currentStage = "INTAKE_ACCEPTED";
  else if (intakeStage === "INTAKE_PENDING") currentStage = "INTAKE_PENDING";
  else currentStage = intakeStage;

  const trustOrFresh =
    workboardStale(input.workboard) || evidenceChainStale(input.evidenceChain) ? "STALE_OR_CHAIN_ISSUE" : "CURRENT";

  const digestFirst =
    digestPrefix(evalBody?.evaluation_sha256) !== "—"
      ? digestPrefix(evalBody?.evaluation_sha256)
      : digestPrefix(genReport?.report_sha256) !== "—"
        ? digestPrefix(genReport?.report_sha256)
        : digestPrefix(lastIntake?.artifact_sha256);

  const generatedAt =
    asString(evalBody?.evaluated_at_utc) ??
    asString(genReport?.generated_at_utc) ??
    asString(intake?.generated_at_utc) ??
    "UNKNOWN";

  const lifecycleId = `${anchor.strategyId}:${anchor.thesisId}:${anchor.intakeId}`.slice(0, 120);

  const hasIntake = intakeCount > 0 || intakeEntries.length > 0;
  const intakeBlocked = readiness === "RESEARCH_INTAKE_BLOCKED";
  const genMissing = genStage === "UNKNOWN" || genStage === "DEGRADED";
  const evalMissing = evalStage === "UNKNOWN" || evalStage === "DEGRADED";
  const genUnreadable = genDegraded.some((c) => c.includes("UNREADABLE"));
  const evalUnreadable = thesisDegraded.some((c) => c.includes("UNREADABLE"));
  const evalBlocked =
    evalUnreadable ||
    (evalBody != null && (support === "FALSIFIED" || kills > 0));
  const evalOkForPaper =
    evalBody &&
    thesisDegraded.length === 0 &&
    support !== "FALSIFIED" &&
    kills === 0 &&
    evalStage === "THESIS_EVALUATED";
  const paperOk = paperStage === "PAPER_TRACKING_LINKED";

  let next: StrategyLifecycleReviewAction = "NO_IMMEDIATE_ACTION";

  if (graveyarded) next = "REVIEW_DEATH_REASON";
  else if (workboardStale(input.workboard) || evidenceChainStale(input.evidenceChain)) next = "REFRESH_EVIDENCE";
  else if (!hasIntake) next = "SUBMIT_STRATEGY_IDEA";
  else if (intakeBlocked) next = "REVIEW_BLOCKERS";
  else if (hasIntake && intakeStage === "DEGRADED") next = "REVIEW_BLOCKERS";
  else if (hasIntake && genMissing && genUnreadable) next = "REVIEW_BLOCKERS";
  else if (hasIntake && genMissing) next = "GENERATE_THESIS";
  else if (genStage === "THESIS_GENERATED" && evalMissing)
    next = evalUnreadable ? "REVIEW_BLOCKERS" : "EVALUATE_THESIS";
  else if (evalBlocked) next = "REVIEW_BLOCKERS";
  else if (evalOkForPaper && paperStage === "DEGRADED") next = "REVIEW_BLOCKERS";
  else if (evalOkForPaper && !paperOk) next = "CONSIDER_PAPER_TRACKING";
  else next = "NO_IMMEDIATE_ACTION";

  return {
    lifecycle_id: lifecycleId,
    strategy_id: anchor.strategyId,
    thesis_id: anchor.thesisId,
    intake_id: anchor.intakeId,
    tracking_id: anchor.trackingId,
    run_id: anchor.runId,
    current_stage: currentStage,
    status: graveyarded ? "GRAVEYARDED" : currentStage,
    trust_or_freshness: trustOrFresh,
    blocker_count: totalBlockers,
    warning_count: totalWarnings,
    digest_prefix: digestFirst,
    generated_at_utc: generatedAt,
    next_review_action: next,
    rows,
  };
}
