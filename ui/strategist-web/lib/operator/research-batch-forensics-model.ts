import { asNumber, asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";

export type ResearchForensicsRow = {
  __id: string;
  section: string;
  run_or_tracking_id: string;
  status: string;
  review_status: "REQUIRES_REVIEW" | "DEGRADED" | "PENDING" | "OK";
  trust: string;
  blocker_count: number;
  warning_count: number;
  digest_prefix: string;
  generated_at_utc: string;
  review_target: string;
  raw: Record<string, unknown>;
};

export type ResearchForensicsModel = {
  rows: ResearchForensicsRow[];
  review_next: ResearchForensicsRow | null;
  totals: {
    requires_review_count: number;
    degraded_count: number;
    pending_count: number;
  };
};

function digestPrefix(input: unknown): string {
  const value = asString(input);
  if (!value) return "—";
  return value.length > 12 ? `${value.slice(0, 12)}...` : value;
}

function scoreReviewStatus(row: ResearchForensicsRow): number {
  if (row.review_status === "REQUIRES_REVIEW") return 400 + row.blocker_count * 10 + row.warning_count;
  if (row.review_status === "DEGRADED") return 300 + row.blocker_count * 10 + row.warning_count;
  if (row.review_status === "PENDING") return 200;
  return 100;
}

function replaySummary(payload: Record<string, unknown> | null | undefined): {
  status: string;
  mismatch: number;
  missing: number;
} {
  const replay = asRecord(payload?.artifact_replay);
  return {
    status: asString(replay?.status) ?? "UNKNOWN",
    mismatch: asNumber(replay?.digest_mismatch_count) ?? 0,
    missing: asNumber(replay?.missing_artifact_count) ?? 0,
  };
}

function inferReviewStatus(opts: {
  degraded: string[];
  blockerCount: number;
  warningCount: number;
  trust: string;
  status: string;
}): ResearchForensicsRow["review_status"] {
  if (opts.blockerCount > 0 || opts.degraded.length > 0) return "DEGRADED";
  const statusUpper = opts.status.toUpperCase();
  const trustUpper = opts.trust.toUpperCase();
  if (
    statusUpper.includes("BLOCK") ||
    statusUpper.includes("FAIL") ||
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

export function buildResearchBatchForensicsModel(input: {
  strategyBatchLatest: unknown;
  strategyBatchesList: unknown;
  backtestForensicsLatest: unknown;
  paperTrackingLatest: unknown;
  strategyGraveyardLatest: unknown;
  strategyMemoryLatest: unknown;
  strategyThesisLatest: unknown;
  shadowBookLatest: unknown;
}): ResearchForensicsModel {
  const rows: ResearchForensicsRow[] = [];

  const batchLatest = asRecord(input.strategyBatchLatest);
  const batchLatestInner = asRecord(batchLatest?.latest);
  const batchLatestDegraded = asStringArray(batchLatest?.degraded);
  {
    const replay = replaySummary(batchLatest);
    const status = batchLatestInner ? (batchLatestInner.ok === true ? "OK" : "REQUIRES_REVIEW") : "PENDING";
    const blockerCount = (asNumber(batchLatestInner?.blocked_count) ?? 0) + replay.mismatch + replay.missing;
    const warningCount = asNumber(batchLatestInner?.failed_count) ?? 0;
    const trust = batchLatestInner ? `BATCH_SUMMARY_PRESENT · REPLAY_${replay.status}` : "UNKNOWN";
    rows.push({
      __id: "latest-batch",
      section: "Latest Batch",
      run_or_tracking_id: asString(batchLatestInner?.run_id) ?? "UNKNOWN",
      status,
      trust,
      blocker_count: blockerCount,
      warning_count: warningCount,
      digest_prefix: digestPrefix(batchLatestInner?.batch_sha256 ?? batchLatest?.summary_path),
      generated_at_utc: asString(batchLatest?.generated_at_utc) ?? "UNKNOWN",
      review_target: asString(batchLatestInner?.top_candidate) ?? "review latest strategy batch",
      review_status: inferReviewStatus({ degraded: batchLatestDegraded, blockerCount, warningCount, trust, status }),
      raw: batchLatest ?? {},
    });
  }

  const forensics = asRecord(input.backtestForensicsLatest);
  const forensicsSummary = asRecord(forensics?.summary);
  const forensicsDegraded = asStringArray(forensics?.degraded);
  {
    const replay = replaySummary(forensics);
    const status = asString(forensicsSummary?.batch_present) === "false" ? "PENDING" : "READY";
    const blockerCount = (asNumber(forensicsSummary?.blocked_count) ?? 0) + replay.mismatch + replay.missing;
    const warningCount =
      (asNumber(forensicsSummary?.needs_evidence_count) ?? 0) + (asNumber(forensicsSummary?.failed_count) ?? 0);
    const trust = blockerCount > 0 ? `RESTRICTED · REPLAY_${replay.status}` : `FORENSICS_PRESENT · REPLAY_${replay.status}`;
    rows.push({
      __id: "backtest-forensics",
      section: "Backtest Forensics",
      run_or_tracking_id: asString(asRecord(forensics?.batch)?.run_id) ?? "UNKNOWN",
      status,
      trust,
      blocker_count: blockerCount,
      warning_count: warningCount,
      digest_prefix: digestPrefix(forensics?.summary_path),
      generated_at_utc: asString(forensics?.generated_at_utc) ?? "UNKNOWN",
      review_target: "review blocked/needs-evidence strategies",
      review_status: inferReviewStatus({ degraded: forensicsDegraded, blockerCount, warningCount, trust, status }),
      raw: forensics ?? {},
    });
  }

  const paper = asRecord(input.paperTrackingLatest);
  const paperLatest = asRecord(paper?.latest);
  const paperManifest = asRecord(paperLatest?.manifest);
  const paperDegraded = asStringArray(paper?.degraded);
  {
    const replay = replaySummary(paper);
    const lifecycle = asString(paperLatest?.lifecycle_state) ?? "UNKNOWN";
    const status = lifecycle === "UNKNOWN" ? "PENDING" : lifecycle;
    const blockers = asStringArray(paperLatest?.lifecycle_blockers).length + replay.mismatch + replay.missing;
    const warnings = asNumber(asRecord(paperLatest?.scorecard)?.warning_count) ?? 0;
    const trust = `${asString(paperManifest?.trust_banner) ?? "UNKNOWN"} · REPLAY_${replay.status}`;
    rows.push({
      __id: "paper-tracking",
      section: "Paper Tracking",
      run_or_tracking_id: asString(paperLatest?.tracking_id) ?? "UNKNOWN",
      status,
      trust,
      blocker_count: blockers,
      warning_count: warnings,
      digest_prefix: digestPrefix(paperManifest?.manifest_sha256 ?? paper?.manifest_path),
      generated_at_utc: asString(paper?.generated_at_utc) ?? "UNKNOWN",
      review_target: "review paper-tracking lifecycle and promotion disclaimers",
      review_status: inferReviewStatus({ degraded: paperDegraded, blockerCount: blockers, warningCount: warnings, trust, status }),
      raw: paper ?? {},
    });
  }

  const graveyard = asRecord(input.strategyGraveyardLatest);
  const graveyardSummary = asRecord(graveyard?.summary);
  const graveyardDegraded = asStringArray(graveyard?.degraded);
  {
    const hardBlocked = asNumber(graveyardSummary?.hard_blocked_count) ?? 0;
    const operatorReview = asNumber(graveyardSummary?.operator_review_count) ?? 0;
    const status = hardBlocked > 0 ? "BLOCKED" : "OK";
    const blockerCount = hardBlocked;
    const warningCount = operatorReview;
    const trust = asString(graveyard?.read_plane_only) === "true" ? "READ_ONLY" : "UNKNOWN";
    rows.push({
      __id: "strategy-graveyard",
      section: "Graveyard",
      run_or_tracking_id: "latest",
      status,
      trust,
      blocker_count: blockerCount,
      warning_count: warningCount,
      digest_prefix: digestPrefix(graveyard?.index_path),
      generated_at_utc: asString(graveyard?.generated_at_utc) ?? "UNKNOWN",
      review_target: "review hard-blocked and operator-review strategies",
      review_status: inferReviewStatus({ degraded: graveyardDegraded, blockerCount, warningCount, trust, status }),
      raw: graveyard ?? {},
    });
  }

  const memory = asRecord(input.strategyMemoryLatest);
  const memoryLatest = asRecord(memory?.latest);
  const memoryDegraded = asStringArray(memory?.degraded);
  {
    const duplicateCount = asNumber(memoryLatest?.duplicate_variant_count) ?? 0;
    const killedCount = asNumber(memoryLatest?.killed_count) ?? 0;
    const status = memoryLatest ? "AVAILABLE" : "PENDING";
    const blockerCount = 0;
    const warningCount = duplicateCount + killedCount;
    const trust = asString(memoryLatest?.index_sha256) ? "INDEX_HASHED" : "UNKNOWN";
    rows.push({
      __id: "strategy-memory",
      section: "Thesis/Memory",
      run_or_tracking_id: "latest",
      status,
      trust,
      blocker_count: blockerCount,
      warning_count: warningCount,
      digest_prefix: digestPrefix(memoryLatest?.index_sha256 ?? memory?.index_path),
      generated_at_utc: asString(memory?.generated_at_utc) ?? "UNKNOWN",
      review_target: "review duplicates/killed variants and memory drift",
      review_status: inferReviewStatus({ degraded: memoryDegraded, blockerCount, warningCount, trust, status }),
      raw: {
        strategy_memory: memory ?? {},
        strategy_thesis: asRecord(input.strategyThesisLatest) ?? {},
        shadow_book: asRecord(input.shadowBookLatest) ?? {},
      },
    });
  }

  const sorted = [...rows].sort((a, b) => scoreReviewStatus(b) - scoreReviewStatus(a));
  return {
    rows,
    review_next: sorted[0] ?? null,
    totals: {
      requires_review_count: rows.filter((r) => r.review_status === "REQUIRES_REVIEW").length,
      degraded_count: rows.filter((r) => r.review_status === "DEGRADED").length,
      pending_count: rows.filter((r) => r.review_status === "PENDING").length,
    },
  };
}
