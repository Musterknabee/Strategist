import { describe, expect, it } from "vitest";
import { buildCandidateWorkbenchModel } from "@/lib/operator/candidate-workbench-model";

function baseInput() {
  return {
    strategyMemoryLatest: null,
    strategyGraveyardLatest: null,
    backtestForensicsLatest: null,
    paperTrackingLatest: null,
    providerSetup: null,
    providerHealth: null,
    evidenceChain: null,
  };
}

describe("buildCandidateWorkbenchModel", () => {
  it("returns empty summary without fabricating wins", () => {
    const model = buildCandidateWorkbenchModel(baseInput());
    expect(model.candidate_count).toBe(0);
    expect(model.paper_win_count).toBe(0);
    expect(model.paper_loss_count).toBe(0);
  });

  it("derives PAPER_WIN from explicit paper return", () => {
    const model = buildCandidateWorkbenchModel({
      ...baseInput(),
      strategyMemoryLatest: {
        generated_at_utc: "2026-05-05T00:00:00Z",
        latest: { memory_records: [{ strategy_id: "strat-a", latest_manifest_sha256: "a".repeat(64) }] },
      },
      paperTrackingLatest: {
        generated_at_utc: "2026-05-05T01:00:00Z",
        latest: {
          tracking_id: "trk-a",
          manifest: { candidate: { strategy_id: "strat-a" } },
          lifecycle_blockers: [],
          scorecard: { cumulative_paper_return: 0.3, warning_count: 0 },
        },
      },
      evidenceChain: { timeline: { entries: [{}] }, degraded: [], summary: { chain_issue_count_total: 0 } },
    });
    expect(model.paper_win_count).toBe(1);
    expect(model.no_paper_data_count).toBe(0);
  });

  it("marks blocked and duplicate warning conservatively", () => {
    const model = buildCandidateWorkbenchModel({
      ...baseInput(),
      strategyMemoryLatest: {
        latest: {
          duplicate_variant_count: 1,
          memory_records: [{ strategy_id: "strat-b" }],
        },
      },
      paperTrackingLatest: {
        latest: {
          tracking_id: "trk-b",
          manifest: { candidate: { strategy_id: "strat-b" } },
          lifecycle_blockers: ["BLOCKED"],
          scorecard: { warning_count: 0 },
        },
      },
      evidenceChain: { timeline: { entries: [] }, degraded: [], summary: { chain_issue_count_total: 0 } },
    });
    expect(model.blocked_count).toBe(1);
    expect(model.duplicate_warning_count).toBe(1);
    expect(model.rows[0]?.paper_result).toBe("BLOCKED");
  });
});
