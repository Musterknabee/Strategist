import { describe, expect, it } from "vitest";
import { buildStrategyLifecycleModel } from "./strategy-lifecycle-model";

const emptyChain = {
  schema_version: "ui_evidence_chain/v1",
  degraded: [],
  summary: {
    chain_issue_count_total: 0,
    decision_ledger_chain_ok: true,
    operator_action_chain_ok: true,
  },
};

const freshWorkboard = {
  schema_version: "ui_workboard_dashboard/v1",
  stats: { freshness_state: "FRESH" },
  materialization: { materialization_state: "READY" },
};

function baseInput(overrides: Partial<Parameters<typeof buildStrategyLifecycleModel>[0]> = {}) {
  return {
    strategyIntakeLatest: null,
    strategyThesisLatest: null,
    strategyThesisGenerationLatest: null,
    strategyMemoryLatest: null,
    strategyGraveyardLatest: null,
    paperTrackingLatest: null,
    backtestForensicsLatest: null,
    strategyBatchLatest: null,
    workboard: freshWorkboard,
    evidenceChain: emptyChain,
    ...overrides,
  };
}

describe("buildStrategyLifecycleModel", () => {
  it("treats empty read-plane as UNKNOWN intake and recommends SUBMIT_STRATEGY_IDEA", () => {
    const m = buildStrategyLifecycleModel(baseInput());
    expect(m.rows[0].stage).toBe("INTAKE_PENDING");
    expect(m.next_review_action).toBe("SUBMIT_STRATEGY_IDEA");
    expect(m.current_stage).toBe("INTAKE_PENDING");
  });

  it("marks intake accepted from readiness_state and moves next action to GENERATE_THESIS when generation missing", () => {
    const m = buildStrategyLifecycleModel(
      baseInput({
        strategyIntakeLatest: {
          schema_version: "ui_strategy_intake/v1",
          generated_at_utc: "2026-05-01T10:00:00Z",
          degraded: [],
          latest: {
            intake_count: 1,
            entries: [
              {
                intake_id: "in-1",
                proposal_id: "pr-1",
                strategy_name: "S-1",
                readiness_state: "RESEARCH_INTAKE_RECORDED",
                artifact_sha256: "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
                created_at_utc: "2026-05-01T09:00:00Z",
                operator_id: "ops",
                target_universe: "u",
                intended_horizon: "d",
                artifact_path: "/tmp/a.json",
              },
            ],
          },
        },
        strategyThesisGenerationLatest: {
          schema_version: "ui_strategy_thesis_generation/v1",
          degraded: ["NO_THESIS_GENERATION_REPORT"],
          latest_generation: null,
        },
        strategyThesisLatest: {
          schema_version: "ui_strategy_thesis/v1",
          degraded: ["NO_THESIS_EVALUATION"],
          latest: null,
        },
      }),
    );
    expect(m.rows[0].stage).toBe("INTAKE_ACCEPTED");
    expect(m.next_review_action).toBe("GENERATE_THESIS");
    expect(m.digest_prefix).not.toBe("—");
  });

  it("recommends EVALUATE_THESIS when generation exists but evaluation file is absent", () => {
    const m = buildStrategyLifecycleModel(
      baseInput({
        strategyIntakeLatest: {
          latest: {
            intake_count: 1,
            entries: [{ readiness_state: "RESEARCH_INTAKE_RECORDED", intake_id: "i1", proposal_id: "p1" }],
          },
          degraded: [],
        },
        strategyThesisGenerationLatest: {
          degraded: [],
          latest_generation: {
            run_id: "r1",
            batch_id: "b1",
            generated_at_utc: "2026-05-01T10:00:00Z",
            generated_count: 1,
            report_sha256: "fedcba0123456789fedcba0123456789fedcba0123456789fedcba0123456789",
            generated_theses: [{ strategy_id: "STRAT-1", thesis_id: "th-1" }],
          },
        },
        strategyThesisLatest: {
          degraded: ["NO_THESIS_EVALUATION"],
          latest: null,
        },
      }),
    );
    expect(m.rows[1].stage).toBe("THESIS_GENERATED");
    expect(m.next_review_action).toBe("EVALUATE_THESIS");
    expect(m.strategy_id).toBe("STRAT-1");
  });

  it("recommends REVIEW_BLOCKERS when evaluation is falsified", () => {
    const m = buildStrategyLifecycleModel(
      baseInput({
        strategyIntakeLatest: {
          latest: { intake_count: 1, entries: [{ readiness_state: "RESEARCH_INTAKE_RECORDED" }] },
          degraded: [],
        },
        strategyThesisGenerationLatest: {
          degraded: [],
          latest_generation: {
            run_id: "r1",
            batch_id: "b1",
            generated_at_utc: "2026-05-01T10:00:00Z",
            generated_count: 1,
            generated_theses: [{ strategy_id: "STRAT-1", thesis_id: "th-1" }],
          },
        },
        strategyThesisLatest: {
          degraded: [],
          latest: {
            strategy_id: "STRAT-1",
            thesis_id: "th-1",
            support_status: "FALSIFIED",
            evaluated_at_utc: "2026-05-01T11:00:00Z",
            evaluation_sha256: "1111111111111111111111111111111111111111111111111111111111111111",
            contradictions: [],
            triggered_kill_criteria: [],
          },
        },
      }),
    );
    expect(m.next_review_action).toBe("REVIEW_BLOCKERS");
  });

  it("recommends REVIEW_DEATH_REASON when anchored strategy is in graveyard entries", () => {
    const m = buildStrategyLifecycleModel(
      baseInput({
        strategyThesisLatest: {
          degraded: [],
          latest: {
            strategy_id: "DEAD-1",
            thesis_id: "t1",
            support_status: "INCONCLUSIVE",
            evaluated_at_utc: "2026-05-01T11:00:00Z",
            evaluation_sha256: "2222222222222222222222222222222222222222222222222222222222222222",
          },
        },
        strategyIntakeLatest: {
          latest: { intake_count: 1, entries: [{ readiness_state: "RESEARCH_INTAKE_RECORDED" }] },
          degraded: [],
        },
        strategyThesisGenerationLatest: {
          degraded: [],
          latest_generation: {
            run_id: "r1",
            batch_id: "b1",
            generated_at_utc: "2026-05-01T10:00:00Z",
            generated_count: 1,
            generated_theses: [{ strategy_id: "DEAD-1", thesis_id: "t1" }],
          },
        },
        strategyGraveyardLatest: {
          degraded: [],
          summary: { entry_count: 1, hard_blocked_count: 1, operator_review_count: 0 },
          entries: [
            {
              strategy_id: "DEAD-1",
              failure_reasons: ["KILLED"],
              kill_reason: "failed robustness",
            },
          ],
        },
      }),
    );
    expect(m.next_review_action).toBe("REVIEW_DEATH_REASON");
    expect(m.rows.find((r) => r.__id === "lifecycle-graveyard")?.stage).toBe("GRAVEYARDED");
  });

  it("recommends CONSIDER_PAPER_TRACKING when evaluation is clean but paper is not linked for strategy", () => {
    const m = buildStrategyLifecycleModel(
      baseInput({
        strategyIntakeLatest: {
          latest: { intake_count: 1, entries: [{ readiness_state: "RESEARCH_INTAKE_RECORDED" }] },
          degraded: [],
        },
        strategyThesisGenerationLatest: {
          degraded: [],
          latest_generation: {
            run_id: "r1",
            batch_id: "b1",
            generated_at_utc: "2026-05-01T10:00:00Z",
            generated_count: 1,
            generated_theses: [{ strategy_id: "STRAT-9", thesis_id: "t9" }],
          },
        },
        strategyThesisLatest: {
          degraded: [],
          latest: {
            strategy_id: "STRAT-9",
            thesis_id: "t9",
            support_status: "SUPPORTED",
            evaluated_at_utc: "2026-05-01T11:00:00Z",
            evaluation_sha256: "3333333333333333333333333333333333333333333333333333333333333333",
          },
        },
        paperTrackingLatest: {
          degraded: [],
          latest: {
            tracking_id: "trk-x",
            lifecycle_state: "ACTIVE",
            manifest: { candidate: { strategy_id: "OTHER" }, manifest_sha256: "abcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcd" },
          },
        },
      }),
    );
    expect(m.next_review_action).toBe("CONSIDER_PAPER_TRACKING");
  });

  it("surfaces digest_full on evaluation row when evaluation_sha256 is present", () => {
    const sha = "4444444444444444444444444444444444444444444444444444444444444444";
    const m = buildStrategyLifecycleModel(
      baseInput({
        strategyThesisLatest: {
          degraded: [],
          latest: {
            strategy_id: "S",
            thesis_id: "T",
            support_status: "SUPPORTED",
            evaluated_at_utc: "2026-05-01T11:00:00Z",
            evaluation_sha256: sha,
          },
        },
      }),
    );
    const evalRow = m.rows.find((r) => r.__id === "lifecycle-thesis-eval");
    expect(evalRow?.digest_full).toBe(sha);
  });
});
