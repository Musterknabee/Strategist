import { describe, expect, it } from "vitest";
import { buildResearchBatchForensicsModel } from "./research-batch-forensics-model";

describe("buildResearchBatchForensicsModel", () => {
  it("returns pending/unknown-safe rows with empty inputs", () => {
    const model = buildResearchBatchForensicsModel({
      strategyBatchLatest: null,
      strategyBatchesList: null,
      backtestForensicsLatest: null,
      paperTrackingLatest: null,
      strategyGraveyardLatest: null,
      strategyMemoryLatest: null,
      strategyThesisLatest: null,
      shadowBookLatest: null,
    });
    expect(model.rows.length).toBe(5);
    expect(model.totals.pending_count).toBeGreaterThan(0);
  });

  it("prioritizes degraded/blocking forensic rows for review next", () => {
    const model = buildResearchBatchForensicsModel({
      strategyBatchLatest: {
        generated_at_utc: "2026-05-01T10:00:00Z",
        latest: { run_id: "run-1", ok: true, blocked_count: 0, failed_count: 0, top_candidate: "S1" },
        artifact_replay: { status: "OK", digest_mismatch_count: 0, missing_artifact_count: 0 },
      },
      strategyBatchesList: { batches: [] },
      backtestForensicsLatest: {
        generated_at_utc: "2026-05-01T11:00:00Z",
        summary_path: "/tmp/forensics.json",
        degraded: ["NO_BATCH_ARTIFACTS"],
        artifact_replay: { status: "DEGRADED", digest_mismatch_count: 1, missing_artifact_count: 0 },
        summary: { blocked_count: 2, needs_evidence_count: 1, failed_count: 0 },
        batch: { run_id: "run-1" },
      },
      paperTrackingLatest: {
        degraded: [],
        artifact_replay: { status: "OK", digest_mismatch_count: 0, missing_artifact_count: 0 },
        latest: { tracking_id: "trk-1", lifecycle_state: "ACTIVE" },
      },
      strategyGraveyardLatest: { degraded: [], summary: { hard_blocked_count: 0, operator_review_count: 0 } },
      strategyMemoryLatest: { degraded: [], latest: { index_sha256: "ab".repeat(32), duplicate_variant_count: 0, killed_count: 0 } },
      strategyThesisLatest: {},
      shadowBookLatest: {},
    });
    expect(model.review_next?.section).toBe("Backtest Forensics");
    expect(model.review_next?.review_status).toBe("DEGRADED");
    expect(model.review_next?.trust).toContain("REPLAY_DEGRADED");
  });
});
