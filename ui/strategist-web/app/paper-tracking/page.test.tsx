/** @vitest-environment jsdom */

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PaperTrackingPage from "./page";

vi.mock("@/lib/config/public-config", () => ({
  tryGetPublicStrategistApiBaseUrl: () => ({ ok: true as const, baseUrl: "http://127.0.0.1:8000" }),
}));

vi.mock("@/hooks/useUiPaperTracking", () => ({
  useUiPaperTrackingLatest: () => ({
    data: {
      schema_version: "ui_paper_tracking/v2",
      latest: {
        tracking_id: "tid1",
        lifecycle_state: "WATCHLIST",
        lifecycle_kill_rule_posture: "NONE",
        lifecycle_basis_summary: "Warnings or warned kill posture — elevated monitoring.",
        lifecycle_blockers: ["PORTFOLIO_DUPLICATIVE_AT_ENROLLMENT"],
        lifecycle_promotion_disclaimer:
          "PROMOTION_REVIEW_READY is an evidence gate only — not live trading approval or deployment promotion.",
        lifecycle_assessment_artifact: null,
        manifest: {
          candidate: {
            strategy_id: "s1",
            batch_id: "b1",
            run_id: "r1",
            paper_posture: "RESEARCH_PAPER_TRACKING",
            synthetic_demo: false,
          },
          portfolio_carry_forward: { portfolio_gate_status: "DUPLICATIVE", duplicate_alpha_warnings: ["DUPLICATE_ALPHA:a:b:0.99"] },
          enrollment_notes: ["PORTFOLIO_BATCH_GATE:DUPLICATIVE"],
        },
        scorecard: {
          kill_state: "WARNED",
          cumulative_paper_return: -0.01,
          drift_score: 0.02,
          execution_realism_decay_level: "WARN",
          scorecard_sha256: "abc123",
          triggered_rules: [],
        },
        signal_history_recent: [
          { summary: { observation_date_utc: "2026-05-01", signal_exposure: 0.5, evidence_sha256: "deadbeef" } },
        ],
        outcome_history_recent: [
          { summary: { observation_date_utc: "2026-05-01", paper_return_1d: 0.001, cumulative_paper_equity_factor: 1.001 } },
        ],
      },
      degraded: [],
      manifest_path: "/tmp/m.json",
    },
    isError: false,
  }),
}));

vi.mock("@/hooks/useTerminalPageBind", () => ({
  useTerminalPageBind: () => {},
}));

vi.mock("@/lib/terminal/cockpit-context", () => ({
  useTerminalCockpit: () => ({
    openInspector: vi.fn(),
    setLastDigest: vi.fn(),
  }),
}));

describe("PaperTrackingPage", () => {
  it("renders paper posture and no live trading copy", () => {
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <PaperTrackingPage />
      </QueryClientProvider>,
    );
    expect(screen.getByText(/Paper tracking/i)).toBeTruthy();
    expect(screen.getByText(/no live trading/i)).toBeTruthy();
    expect(screen.getAllByText("s1").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/DUPLICATIVE/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText("WATCHLIST").length).toBeGreaterThan(0);
    expect(screen.getByText(/not live approval/i)).toBeTruthy();
  });
});
