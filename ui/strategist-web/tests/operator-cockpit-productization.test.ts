import { describe, expect, it } from "vitest";
import { buildCandidateWorkbenchModel } from "@/lib/operator/candidate-workbench-model";
import { buildOperatorHomeSummary } from "@/lib/operator/operator-home-summary-model";

const memory = { generated_at_utc: "2026-05-01T10:00:00Z", latest: { duplicate_variant_count: 0, memory_records: [{ strategy_id: "STRAT-A", latest_manifest_sha256: "abcdef0123456789", updated_at_utc: "2026-05-01T10:00:00Z" }] } };
const forensics = { generated_at_utc: "2026-05-01T10:00:00Z", strategies: [{ strategy_id: "STRAT-A", artifacts: { observed_sha256: { report: "abcdef" } }, blockers: [], warnings: [] }] };
const evidenceChainOk = { generated_at_utc: "2026-05-01T10:00:00Z", degraded: [], summary: { chain_issue_count_total: 0 }, timeline: { entries: [{ id: "e1" }] } };

function paper(cumulative: number | undefined, blockers: string[] = []) {
  return { generated_at_utc: "2026-05-01T10:00:00Z", degraded: [], latest: { tracking_id: "trk-1", lifecycle_blockers: blockers, manifest: { candidate: { strategy_id: "STRAT-A" } }, scorecard: cumulative === undefined ? {} : { cumulative_paper_return: cumulative, warning_count: 0 } } };
}

function candidateModel(overrides: Partial<Parameters<typeof buildCandidateWorkbenchModel>[0]> = {}) {
  return buildCandidateWorkbenchModel({ strategyMemoryLatest: memory, strategyGraveyardLatest: { entries: [] }, backtestForensicsLatest: forensics, paperTrackingLatest: paper(undefined), providerSetup: { summary: { missing_secret_count: 0 } }, providerHealth: { entries: [{ classified_status: "OK" }] }, evidenceChain: evidenceChainOk, ...overrides });
}

describe("operator cockpit productization semantics", () => {
  it("keeps missing paper data explicit instead of treating it as OK", () => {
    const model = candidateModel({ paperTrackingLatest: { latest: null } });
    expect(model.rows[0].paper_result).toBe("NO_PAPER_DATA");
    expect(model.next_action).toBe("RUN_PAPER_TRACKING");
    expect(JSON.stringify(model)).not.toContain('"paper_result":"OK"');
  });

  it("classifies explicit positive and negative paper return without claiming quality", () => {
    expect(candidateModel({ paperTrackingLatest: paper(0.12) }).rows[0].paper_result).toBe("PAPER_WIN");
    expect(candidateModel({ paperTrackingLatest: paper(-0.04) }).rows[0].paper_result).toBe("PAPER_LOSS");
  });

  it("lets explicit blockers take precedence over optimistic paper results", () => {
    const model = candidateModel({ paperTrackingLatest: paper(0.12, ["POLICY_BLOCKED"]) });
    expect(model.rows[0].paper_result).toBe("BLOCKED");
    expect(model.rows[0].lifecycle_state).toBe("BLOCKED");
    expect(model.next_action).toBe("REVIEW_CANDIDATE");
  });

  it("treats pending provider keys as action-required rather than success", () => {
    const model = candidateModel({ providerSetup: { summary: { missing_secret_count: 1 } } });
    expect(model.rows[0].provider_status).toBe("PENDING_KEY");
    expect(model.rows[0].next_action).toBe("ADD_PROVIDER_KEY");
    expect(model.next_action).toBe("ADD_PROVIDER_KEY");
  });

  it("surfaces degraded replay/evidence as degraded, not OK", () => {
    const model = candidateModel({ evidenceChain: { degraded: ["DIGEST_MISMATCH"], summary: { chain_issue_count_total: 1 }, timeline: { entries: [] } } });
    expect(model.rows[0].replay_status).toBe("DIGEST_MISMATCH");
    expect(model.replay_problem_count).toBe(1);
  });

  it("keeps Operator Home missing data as UNKNOWN or NO_PAPER_DATA", () => {
    const summary = buildOperatorHomeSummary({ strategyIntakeLatest: null, strategyThesisLatest: null, strategyThesisGenerationLatest: null, strategyMemoryLatest: null, strategyGraveyardLatest: null, paperTrackingLatest: null, backtestForensicsLatest: null, strategyBatchLatest: null, workboard: null, evidenceChain: null, providerHealth: null, providerSetup: null, anyError: false });
    expect(summary.strategy_count).toBeNull();
    expect(summary.strategy_rows[0].paper_result).toBe("NO_PAPER_DATA");
    expect(summary.overall_status).toBe("UNKNOWN");
  });
});
