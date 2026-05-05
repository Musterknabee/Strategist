import { describe, expect, it } from "vitest";
import { buildPromotionDossierModel } from "./promotion-dossier-model";

const emptyInput = {
  readyzBody: null,
  strategyIntakeLatest: null,
  strategyThesisLatest: null,
  strategyThesisGenerationLatest: null,
  paperTrackingLatest: null,
  strategyBatchLatest: null,
  backtestForensicsLatest: null,
  evidenceChain: null,
  operatorActions: null,
  workboard: null,
  evidence: null,
  paperExecution: null,
  queryFailed: false,
};

describe("buildPromotionDossierModel", () => {
  it("renders UNKNOWN posture fields with no data", () => {
    const m = buildPromotionDossierModel(emptyInput);
    expect(m.current_state).toBe("UNKNOWN");
    expect(m.ledger_event_hash).toBe("UNKNOWN");
    expect(m.gate_rows.length).toBe(0);
    expect(m.recommended_review_action).toBe("FIND_EXPERIMENT_EVIDENCE");
  });

  it("counts gate pass/fail from gate_matrix", () => {
    const m = buildPromotionDossierModel({
      ...emptyInput,
      strategyThesisLatest: {
        latest: { strategy_id: "S1", thesis_id: "T1", support_status: "OK" },
        degraded: [],
      },
      backtestForensicsLatest: {
        degraded: [],
        summary: { batch_present: true },
        strategies: [
          {
            strategy_id: "S1",
            gate_matrix: {
              robustness_gate: "PASS",
              execution_realism_gate: "FAIL",
              promotion_eligible: false,
            },
            blockers: ["X"],
            warnings: [],
            data_plane: "REAL_LOCAL",
            pit_status: "OK",
            data_status: "OK",
          },
        ],
      },
      evidenceChain: {
        summary: { decision_ledger_chain_ok: true },
        streams: {
          decision_ledger: {
            entries: [
              {
                experiment_id: "S1",
                promotion_state: "CONDITIONAL",
                event_type: "adjudication",
                sequence_number: 2,
                event_hash: "aaabbbcccdddeeefff0011223344556677889900aabbccddeeff0011223344",
                previous_event_hash: "1111",
                manifest_hash: "2222",
                payload_digest_sha256: "3333",
                writer_identity: "orchestrator",
                chained: true,
                issue_codes: [],
              },
              {
                experiment_id: "S1",
                promotion_state: "QUARANTINED",
                event_type: "adjudication",
                sequence_number: 1,
                event_hash: "prevhash000000000000000000000000000000000000000000000000000000",
                previous_event_hash: "genesis",
                chained: true,
                issue_codes: [],
              },
            ],
          },
        },
      },
    });
    expect(m.current_state).toBe("CONDITIONAL");
    expect(m.previous_state).toBe("QUARANTINED");
    expect(m.gate_pass_count).toBeGreaterThanOrEqual(1);
    expect(m.gate_fail_count).toBeGreaterThanOrEqual(1);
    expect(m.ledger_event_hash).toContain("aaabbb");
    expect(m.recommended_review_action).toBe("REVIEW_FAILED_GATES");
  });

  it("recommends REVIEW_LEDGER_CHAIN when chain broken", () => {
    const m = buildPromotionDossierModel({
      ...emptyInput,
      strategyThesisLatest: { latest: { strategy_id: "S1" }, degraded: [] },
      evidenceChain: {
        summary: { decision_ledger_chain_ok: false },
        streams: {
          decision_ledger: {
            entries: [
              {
                experiment_id: "S1",
                promotion_state: "PROMOTABLE",
                event_type: "x",
                sequence_number: 1,
                event_hash: "h1",
                chained: false,
                issue_codes: ["HASH_MISMATCH"],
              },
            ],
          },
        },
      },
    });
    expect(m.chain_status).toBe("DEGRADED");
    expect(m.recommended_review_action).toBe("REVIEW_LEDGER_CHAIN");
  });

  it("surfaces benchmark and robustness lines when present", () => {
    const m = buildPromotionDossierModel({
      ...emptyInput,
      strategyThesisLatest: { latest: { strategy_id: "S1" }, degraded: [] },
      backtestForensicsLatest: {
        strategies: [
          {
            strategy_id: "S1",
            metrics: { benchmark_id: "SPY", benchmark_delta: 0.1 },
            gate_matrix: { robustness_gate: "PASS", cpcv_robustness_gate: "PASS", execution_realism_gate: "PASS" },
            robustness: { pbo_like_score: 0.2, dsr_like_score: 0.4 },
            execution_realism: { model_label: "m1", estimated_slippage_bps: 10 },
            data_plane: "REAL_LOCAL",
            pit_status: "OK",
            data_status: "OK",
          },
        ],
      },
    });
    expect(m.benchmark_lines.some((l) => l.includes("SPY"))).toBe(true);
    expect(m.robustness_lines.some((l) => l.includes("pbo"))).toBe(true);
    expect(m.execution_realism_lines.some((l) => l.includes("slippage"))).toBe(true);
  });
});
