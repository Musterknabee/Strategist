/** @vitest-environment jsdom */

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PaperTrackingPage from "./page";

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { gcTime: Infinity, retry: false },
    },
  });
}

vi.mock("@/lib/config/public-config", () => ({
  tryGetPublicStrategistApiBaseUrl: () => ({ ok: true as const, baseUrl: "http://127.0.0.1:8000" }),
}));

vi.mock("@/hooks/useUiPaperTracking", () => ({
  useUiPaperTrackingLatest: () => ({
    data: {
      schema_version: "ui_paper_tracking/v2",
      latest: {
        tracking_id: "tid-promo",
        lifecycle_state: "PROMOTION_REVIEW_READY",
        lifecycle_kill_rule_posture: "NONE",
        lifecycle_basis_summary: "Paper evidence meets promotion-review gate (not approval).",
        lifecycle_blockers: [],
        lifecycle_promotion_disclaimer:
          "PROMOTION_REVIEW_READY is an evidence gate only — not live trading approval or deployment promotion.",
        lifecycle_assessment_artifact: null,
        manifest: {
          candidate: {
            strategy_id: "s-promo",
            batch_id: "b",
            run_id: "r",
            paper_posture: "RESEARCH_PAPER_TRACKING",
            synthetic_demo: false,
          },
          portfolio_carry_forward: { portfolio_gate_status: "NOT_APPLICABLE" },
          enrollment_notes: [],
        },
        scorecard: {
          kill_state: "ACTIVE",
          cumulative_paper_return: 0.01,
          drift_score: 0.02,
          execution_realism_decay_level: "NONE",
          scorecard_sha256: "abc",
          triggered_rules: [],
        },
        signal_history_recent: [],
        outcome_history_recent: [],
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

describe("PaperTrackingPage promotion banner", () => {
  it("renders promotion review gate banner and not-approval copy", () => {
    const client = createQueryClient();
    const view = render(
      <QueryClientProvider client={client}>
        <PaperTrackingPage />
      </QueryClientProvider>,
    );
    expect(screen.getByText(/Promotion review gate/i)).toBeTruthy();
    expect(screen.getByText(/not live trading approval/i)).toBeTruthy();
    expect(screen.getAllByText("PROMOTION_REVIEW_READY").length).toBeGreaterThan(0);
    view.unmount();
    client.clear();
  });
});
