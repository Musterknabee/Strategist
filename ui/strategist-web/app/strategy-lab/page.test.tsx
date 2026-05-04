/** @vitest-environment jsdom */

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import StrategyLabPage from "./page";

vi.mock("@/lib/config/public-config", () => ({
  tryGetPublicStrategistApiBaseUrl: () => ({ ok: true as const, baseUrl: "http://127.0.0.1:8000" }),
}));

const openInspector = vi.fn();

vi.mock("@/hooks/useUiStrategyBatches", () => ({
  useUiStrategyBatchLatest: () => ({
    data: {
      schema_version: "ui_strategy_batch/v1",
      latest: {
        batch_id: "b1",
        run_id: "r1",
        ok: true,
        strategy_count: 4,
        passed_count: 1,
        paper_only_count: 1,
        failed_count: 0,
        blocked_count: 2,
        generated_at_utc: "2026-05-01T12:00:00+00:00",
        top_candidate: { strategy_id: "real-1", rank: 1, score: 2.5 },
        promotion_blocked_counts: { SYNTHETIC_DEMO: 1, ROBUSTNESS: 1 },
        portfolio_correlation_summary: {
          portfolio_gate_status: "NOT_APPLICABLE",
          average_correlation: 0,
          high_correlation_pairs: [],
        },
        batch_ranking: [
          { strategy_id: "real-1", rank: 1, score: 2.5, status: "PASSED", blocked_tier: false },
          { strategy_id: "s1", rank: 2, score: -0.5, status: "PAPER_ONLY", blocked_tier: false },
          { strategy_id: "rob-blocked", rank: 3, score: -1e6, status: "BLOCKED", blocked_tier: true },
          { strategy_id: "er-blocked", rank: 4, score: -1e6, status: "BLOCKED", blocked_tier: true },
        ],
        strategies: [
          {
            strategy_id: "s1",
            status: "PAPER_ONLY",
            pit_status: "SYNTHETIC",
            data_plane: "SYNTHETIC",
            pit_snapshot_status: null,
            data_status: "SYNTHETIC_DEMO",
            adjudication_status: "NOT_INVOKED",
            evidence_manifest_sha256: "abcd1234",
            warnings: ["SYNTHETIC_DEMO_DATA"],
            robustness_gate_status: "NOT_APPLICABLE",
            robustness_model_label: "WALK_FORWARD_LOCAL_BAR_MODEL",
            data_quality_gate_status: "NOT_APPLICABLE",
            parameter_sensitivity_gate_status: "NOT_APPLICABLE",
            regime_analysis_gate_status: "NOT_APPLICABLE",
            gate_summary: {
              promotion_eligible: false,
              promotion_blocked_reasons: ["SYNTHETIC_DEMO"],
              robustness_gate: "NOT_APPLICABLE",
              data_quality_gate: "NOT_APPLICABLE",
              parameter_sensitivity_gate: "NOT_APPLICABLE",
              regime_analysis_gate: "NOT_APPLICABLE",
            },
          },
          {
            strategy_id: "real-1",
            status: "PASSED",
            pit_status: "PIT_VERIFIED",
            data_plane: "REAL_LOCAL",
            pit_snapshot_status: "PIT_VERIFIED",
            data_status: "LOCAL_BARS",
            bars_row_count: 120,
            data_snapshot_digest: "deadbeef0123456789abcdef0123456789abcdef0123456789abcdef01234567",
            data_snapshot_manifest_path: "/tmp/data_snapshot_manifest.json",
            adjudication_status: "NOT_INVOKED",
            evidence_manifest_sha256: "effe",
            warnings: [],
            execution_realism_gate: "PROVEN",
            execution_realism_model_label: "CONSERVATIVE_LOCAL_BAR_MODEL",
            execution_realism_est_slippage_bps: 5,
            execution_realism_est_fee_bps: 1,
            execution_realism_capacity_notional: 250000,
            execution_realism_est_participation: 0.02,
            execution_realism_digest: "abcexecution",
            robustness_gate_status: "PROVEN",
            robustness_model_label: "WALK_FORWARD_LOCAL_BAR_MODEL",
            robustness_evidence_sha256: "robdigest012",
            robustness_fold_count: 4,
            positive_fold_ratio: 0.75,
            worst_fold_return: -0.02,
            pbo_like_score: 0.12,
            dsr_like_score: 0.35,
            analytics_score: 2.5,
            analytics_rank: 1,
            analytics_rank_explanation: "base_risk_adj=2.5; → score (heuristic).",
            equity_curve_path: "/artifacts/equity_curve.json",
            charts_compact: {
              schema_version: "strategy_lab_charts_compact/v1",
              equity: { t: ["2026-01-01", "2026-01-02", "2026-01-03"], v: [1, 1.01, 1.02] },
              drawdown: { t: ["2026-01-01", "2026-01-02", "2026-01-03"], v: [0, 0.005, 0.002] },
              rolling: { t: [], sharpe_like: [], volatility: [] },
              folds: [{ fold_index: 0, test_return: 0.02, train_return: 0.01 }],
              scatter: { total_return: 0.04, max_drawdown: 0.02 },
              digests: { equity_curve: "abc" },
            },
            metrics: { total_return: 0.04, max_drawdown: 0.02 },
            data_quality_gate_status: "PROVEN",
            parameter_sensitivity_gate_status: "STABLE",
            regime_analysis_gate_status: "PROVEN",
            gate_summary: {
              promotion_eligible: true,
              promotion_blocked_reasons: [],
              pit_gate: "PIT_VERIFIED",
              data_gate: "LOCAL_HISTORICAL_BARS",
              data_quality_gate: "PROVEN",
              data_coverage_gate: "PASS",
              robustness_gate: "PROVEN",
              execution_realism_gate: "PROVEN",
              parameter_sensitivity_gate: "STABLE",
              regime_analysis_gate: "PROVEN",
            },
          },
          {
            strategy_id: "rob-blocked",
            status: "BLOCKED",
            pit_status: "PIT_VERIFIED",
            data_plane: "REAL_LOCAL",
            data_status: "LOCAL_BARS",
            execution_realism_gate: "PROVEN",
            robustness_gate_status: "BLOCKED",
            robustness_fold_count: 3,
            metrics: { total_return: -0.01, max_drawdown: 0.15 },
            charts_compact: {
              schema_version: "strategy_lab_charts_compact/v1",
              scatter: { total_return: -0.01, max_drawdown: 0.15 },
            },
            gate_summary: {
              promotion_eligible: false,
              promotion_blocked_reasons: ["ROBUSTNESS:BLOCKED"],
              execution_realism_gate: "PROVEN",
              robustness_gate: "BLOCKED",
              pit_gate: "PIT_VERIFIED",
            },
          },
          {
            strategy_id: "er-blocked",
            status: "BLOCKED",
            pit_status: "PIT_VERIFIED",
            data_plane: "REAL_LOCAL",
            data_status: "LOCAL_BARS",
            execution_realism_gate: "BLOCKED",
            gate_summary: {
              promotion_eligible: false,
              promotion_blocked_reasons: ["EXECUTION_REALISM_NOT_PROVEN"],
              execution_realism_gate: "BLOCKED",
              pit_gate: "PIT_VERIFIED",
            },
          },
        ],
      },
      degraded: [],
    },
    isError: false,
  }),
  useUiStrategyBatchList: () => ({ data: { batches: [] }, isError: false }),
}));

vi.mock("@/hooks/useTerminalPageBind", () => ({
  useTerminalPageBind: () => {},
}));

vi.mock("@/lib/terminal/cockpit-context", () => ({
  useTerminalCockpit: () => ({
    openInspector,
    setLastDigest: vi.fn(),
  }),
}));

describe("StrategyLabPage", () => {
  it("renders synthetic warning and strategy row", () => {
    openInspector.mockClear();
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <StrategyLabPage />
      </QueryClientProvider>,
    );
    expect(screen.getByText(/Strategy Lab/i)).toBeTruthy();
    expect(screen.getByText(/Synthetic demo data/i)).toBeTruthy();
    expect(screen.getAllByText("s1").length).toBeGreaterThan(0);
  });

  it("renders real-data row with PIT_VERIFIED and REAL badge", () => {
    openInspector.mockClear();
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <StrategyLabPage />
      </QueryClientProvider>,
    );
    expect(screen.getAllByText("real-1").length).toBeGreaterThan(0);
    expect(screen.getAllByText("PIT_VERIFIED").length).toBeGreaterThan(0);
    expect(screen.getAllByText("REAL").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Real local bars/i).length).toBeGreaterThan(0);
  });

  it("renders execution realism PROVEN and BLOCKED badges", () => {
    openInspector.mockClear();
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <StrategyLabPage />
      </QueryClientProvider>,
    );
    const proven = screen.getAllByText("PROVEN");
    expect(proven.length).toBeGreaterThan(0);
    const blocked = screen.getAllByText("BLOCKED");
    expect(blocked.length).toBeGreaterThan(0);
  });

  it("inspector payload includes data snapshot digest", () => {
    openInspector.mockClear();
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <StrategyLabPage />
      </QueryClientProvider>,
    );
    fireEvent.click(screen.getAllByText("real-1")[0]);
    expect(openInspector).toHaveBeenCalled();
    const payload = openInspector.mock.calls[0][0] as {
      rawJson: { data_snapshot_inspector?: { digest?: string } };
    };
    expect(payload.rawJson.data_snapshot_inspector?.digest?.startsWith("deadbeef")).toBe(true);
  });

  it("renders robustness PROVEN and BLOCKED badges", () => {
    openInspector.mockClear();
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <StrategyLabPage />
      </QueryClientProvider>,
    );
    const proven = screen.getAllByText("PROVEN");
    expect(proven.length).toBeGreaterThan(0);
    expect(screen.getAllByText("BLOCKED").length).toBeGreaterThan(0);
  });

  it("inspector includes robustness fields", () => {
    openInspector.mockClear();
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <StrategyLabPage />
      </QueryClientProvider>,
    );
    fireEvent.click(screen.getAllByText("real-1")[0]);
    const payload = openInspector.mock.calls[0][0] as {
      rawJson: { robustness_inspector?: { gate_status?: string; explanation?: string } };
    };
    expect(payload.rawJson.robustness_inspector?.gate_status).toBe("PROVEN");
    expect(payload.rawJson.robustness_inspector?.explanation).toMatch(/walk-forward/i);
  });

  it("inspector shows promotion blocked for robustness", () => {
    openInspector.mockClear();
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <StrategyLabPage />
      </QueryClientProvider>,
    );
    fireEvent.click(screen.getAllByText("rob-blocked")[0]);
    const payload = openInspector.mock.calls[0][0] as {
      rawJson: { promotion_blocked_reasons?: string[] };
    };
    expect(payload.rawJson.promotion_blocked_reasons).toContain("ROBUSTNESS:BLOCKED");
  });

  it("inspector includes execution realism slippage and capacity", () => {
    openInspector.mockClear();
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <StrategyLabPage />
      </QueryClientProvider>,
    );
    fireEvent.click(screen.getAllByText("real-1")[0]);
    const payload = openInspector.mock.calls[0][0] as {
      rawJson: { execution_realism_inspector?: { estimated_slippage_bps?: number; capacity_notional?: number } };
    };
    expect(payload.rawJson.execution_realism_inspector?.estimated_slippage_bps).toBe(5);
    expect(payload.rawJson.execution_realism_inspector?.capacity_notional).toBe(250000);
  });

  it("renders analytics charts and batch ranking", () => {
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <StrategyLabPage />
      </QueryClientProvider>,
    );
    const charts = screen.getAllByTestId("strategy-lab-charts");
    expect(charts.length).toBeGreaterThanOrEqual(1);
    const text = charts.map((c) => c.textContent).join("\n");
    expect(text).toMatch(/Batch ranking/i);
    expect(text).toMatch(/Equity \(toy evaluator\)/i);
    expect(text).toMatch(/Gate matrix/i);
  });

  it("inspector includes gauntlet artifact gates", () => {
    openInspector.mockClear();
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <StrategyLabPage />
      </QueryClientProvider>,
    );
    fireEvent.click(screen.getAllByText("real-1")[0]);
    const payload = openInspector.mock.calls[0][0] as {
      rawJson: { gauntlet_inspector?: { data_quality_gate?: string } };
    };
    expect(payload.rawJson.gauntlet_inspector?.data_quality_gate).toBe("PROVEN");
  });

  it("inspector includes chart_inspector with evidence paths", () => {
    openInspector.mockClear();
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <StrategyLabPage />
      </QueryClientProvider>,
    );
    fireEvent.click(screen.getAllByText("real-1")[0]);
    const payload = openInspector.mock.calls[0][0] as {
      rawJson: { chart_inspector?: { equity_curve_path?: string } };
    };
    expect(payload.rawJson.chart_inspector?.equity_curve_path).toContain("equity_curve.json");
  });
});
