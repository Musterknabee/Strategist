import { describe, expect, it } from "vitest";
import {
  buildPolicyRiskGatesModel,
  filterPolicyRiskGatesByCategory,
  interpretRiskLiteral,
} from "./policy-risk-gates-model";
import type { UiMutationSafetyStatus } from "@/lib/api/types";

describe("interpretRiskLiteral", () => {
  it("maps missing to UNKNOWN", () => {
    expect(interpretRiskLiteral(undefined)).toBe("UNKNOWN");
  });
  it("does not treat NOT_RUN as PASS", () => {
    expect(interpretRiskLiteral("NOT_RUN")).toBe("UNKNOWN");
  });
});

describe("buildPolicyRiskGatesModel", () => {
  it("returns UNKNOWN posture when no evidence", () => {
    const m = buildPolicyRiskGatesModel({
      readyzBody: null,
      readyzError: false,
      runtimeBody: null,
      mutationSafety: null,
      facade: null,
      evidence: null,
      operatorActions: null,
      providerHealth: null,
      backtestForensics: null,
      paperExecution: null,
      paperTracking: null,
      queryFailed: false,
    });
    expect(m.posture).toBe("UNKNOWN");
    expect(m.counts.unknown).toBeGreaterThan(0);
    expect(m.gates.some((g) => g.gate_id === "auth.mutation_surface")).toBe(true);
  });

  it("marks readiness blockers as BLOCKED posture", () => {
    const m = buildPolicyRiskGatesModel({
      readyzBody: {
        status: "DEGRADED",
        blockers: [{ code: "LEDGER_PATH", message: "missing", remediation_hint: "fix path" }],
        warnings: [],
      },
      readyzError: false,
      runtimeBody: {},
      mutationSafety: {
        runtime_mode: "DEV",
        authorization_mode: "NON_PRODUCTION_BYPASS",
        token_configured: false,
        mutation_routes_safe: true,
        detail_code: "X",
      },
      facade: { read_plane_only: true },
      evidence: {},
      operatorActions: {},
      providerHealth: { entries: [] },
      backtestForensics: null,
      paperExecution: null,
      paperTracking: null,
      queryFailed: false,
    });
    expect(m.posture).toBe("BLOCKED");
    expect(m.blocker_lines.some((l) => l.includes("LEDGER_PATH"))).toBe(true);
  });

  it("marks production auth misconfiguration as CRITICAL", () => {
    const ms: UiMutationSafetyStatus = {
      runtime_mode: "production",
      authorization_mode: "MISCONFIGURED",
      token_configured: false,
      mutation_routes_safe: false,
      detail_code: "MUTATION_AUTH_NOT_CONFIGURED",
    };
    const m = buildPolicyRiskGatesModel({
      readyzBody: { status: "READY", blockers: [], warnings: [] },
      readyzError: false,
      runtimeBody: { generated_at_utc: "2026-01-01T00:00:00Z", mutation_safety: ms },
      mutationSafety: ms,
      facade: { read_plane_only: true },
      evidence: {},
      operatorActions: { chain_ok: true },
      providerHealth: { entries: [] },
      backtestForensics: null,
      paperExecution: null,
      paperTracking: null,
      queryFailed: false,
    });
    expect(m.gates.filter((g) => g.status === "CRITICAL").length).toBeGreaterThanOrEqual(2);
    expect(m.posture).toBe("BLOCKED");
  });

  it("treats provider AUTH_FAILED as FAIL on provider gate", () => {
    const m = buildPolicyRiskGatesModel({
      readyzBody: { status: "READY", blockers: [], warnings: [] },
      readyzError: false,
      runtimeBody: {},
      mutationSafety: {
        runtime_mode: "DEV",
        authorization_mode: "NON_PRODUCTION_BYPASS",
        token_configured: false,
        mutation_routes_safe: true,
        detail_code: "OK",
      },
      facade: { read_plane_only: true },
      evidence: {},
      operatorActions: {},
      providerHealth: {
        entries: [{ provider_id: "x", classified_status: "AUTH_FAILED" }],
        execution_workflow_blockers: [],
      },
      backtestForensics: null,
      paperExecution: null,
      paperTracking: null,
      queryFailed: false,
    });
    const g = m.gates.find((x) => x.gate_id === "provider.freshness_matrix");
    expect(g?.status).toBe("FAIL");
  });

  it("aggregates forensics robustness and execution gates when batch present", () => {
    const m = buildPolicyRiskGatesModel({
      readyzBody: { status: "READY", blockers: [], warnings: [] },
      readyzError: false,
      runtimeBody: {},
      mutationSafety: {
        runtime_mode: "DEV",
        authorization_mode: "NON_PRODUCTION_BYPASS",
        token_configured: false,
        mutation_routes_safe: true,
        detail_code: "OK",
      },
      facade: { read_plane_only: true },
      evidence: {},
      operatorActions: {},
      providerHealth: { entries: [] },
      backtestForensics: {
        degraded: [],
        generated_at_utc: "2026-01-01T00:00:00Z",
        summary: { batch_present: true },
        strategies: [
          {
            strategy_id: "s1",
            status: "PASSED",
            gate_matrix: {
              robustness_gate: "PASS",
              cpcv_robustness_gate: "PASS",
              execution_realism_gate: "PASS",
              promotion_eligible: true,
              benchmark_id: "SPY",
            },
            metrics: { benchmark_id: "SPY", benchmark_delta: 0.02 },
            robustness: { pbo_like_score: 0.1, dsr_like_score: 0.5 },
            execution_realism: {},
            data_plane: "REAL_LOCAL",
            pit_status: "OK",
            data_status: "OK",
            promotion_blocked_reasons: [],
            blockers: [],
          },
        ],
      },
      paperExecution: { no_live_trading: true, summary: {} },
      paperTracking: null,
      queryFailed: false,
    });
    expect(m.robustness_summary).toContain("PASS");
    expect(m.execution_realism_summary).toContain("PASS");
    const bench = m.gates.find((x) => x.gate_id === "benchmark.context");
    expect(bench?.status).toBe("PASS");
  });

  it("does not treat PBO scores alone as PASS for decoy gate", () => {
    const m = buildPolicyRiskGatesModel({
      readyzBody: { status: "READY", blockers: [], warnings: [] },
      readyzError: false,
      runtimeBody: {},
      mutationSafety: {
        runtime_mode: "DEV",
        authorization_mode: "NON_PRODUCTION_BYPASS",
        token_configured: false,
        mutation_routes_safe: true,
        detail_code: "OK",
      },
      facade: { read_plane_only: true },
      evidence: {},
      operatorActions: {},
      providerHealth: { entries: [] },
      backtestForensics: {
        degraded: [],
        summary: { batch_present: true },
        strategies: [
          {
            strategy_id: "s1",
            status: "PASSED",
            gate_matrix: { robustness_gate: "PASS", cpcv_robustness_gate: "PASS", execution_realism_gate: "PASS" },
            robustness: { pbo_like_score: 0.05 },
            data_plane: "REAL_LOCAL",
            pit_status: "OK",
            data_status: "OK",
            promotion_blocked_reasons: [],
            blockers: [],
          },
        ],
      },
      paperExecution: null,
      paperTracking: null,
      queryFailed: false,
    });
    const decoy = m.gates.find((g) => g.gate_id === "robustness.pbo_dsr_decoy");
    expect(decoy?.status).toBe("UNKNOWN");
  });
});

describe("filterPolicyRiskGatesByCategory", () => {
  it("filters by category", () => {
    const gates = [
      { gate_id: "a", category: "Readiness" },
      { gate_id: "b", category: "Auth Safety" },
    ] as import("./policy-risk-gates-model").RiskGateEntry[];
    expect(filterPolicyRiskGatesByCategory(gates, "Readiness")).toHaveLength(1);
    expect(filterPolicyRiskGatesByCategory(gates, "ALL")).toHaveLength(2);
  });
});
