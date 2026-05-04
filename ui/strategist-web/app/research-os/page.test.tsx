/** @vitest-environment jsdom */

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ResearchOsPage from "./page";

vi.mock("@/hooks/useUiResearchOsStatus", () => ({
  useUiResearchOsStatus: () => ({
    data: {
      schema_version: "ui_research_os_status/v1",
      generated_at_utc: "2026-05-01T00:00:00+00:00",
      degraded: ["NO_PORTFOLIO_ALLOCATION_ARTIFACT"],
      warnings: [],
      artifact_root_summary: {
        artifact_root: "/var/lib/x/artifacts",
        strategy_batch_scan_root: "/var/lib/x/artifacts/strategy_runs",
        paper_tracking_scan_root: "/var/lib/x/artifacts/paper_tracking",
        strategy_data_root: "/var/lib/x/artifacts/strategy_data",
      },
      runtime_demo_manifest: { status: "NOT_PRESENT", artifact_path: "/y" },
      gauntlet_latest: {
        batch_id: "b1",
        run_id: "r1",
        ok: true,
        strategy_count: 2,
        passed_count: 0,
        paper_only_count: 2,
      },
      paper_tracking_latest: {
        latest: {
          tracking_id: "tid1",
          lifecycle_state: "PAPER_TRACKING",
          promotion_review_ready: false,
        },
      },
      promotion_packet_latest: { recommendation: "DO_NOT_PROMOTE" },
      lifecycle_latest: { state: "PAPER_TRACKING" },
      paper_broker_status: { policy_status: "PENDING_KEY" },
      compute_status: { research_compute_readiness: "CPU_FALLBACK_READY", gpu_probe: { gpu_available: false } },
      demo_manifest: { status: "NOT_PRESENT", artifact_path: "/x" },
      provider_ingestion_latest: { status: "ARTIFACT_PRESENT", provider_status: "PENDING_KEY" },
      provider_paper_loop_latest: { status: "NOT_PRESENT", artifact_path: "/z" },
      provider_historical_snapshot_latest: { status: "NOT_PRESENT" },
      paper_broker_status_latest: { status: "NOT_PRESENT" },
      provider_backed_gauntlet_latest: {
        provider_snapshot_strategy_count: 0,
        has_provider_strategies: false,
      },
      daily_tracking_latest: {},
      cpcv_latest: { status: "NO_CPCV_FIELDS" },
      portfolio_allocation_latest: null,
    },
    isLoading: false,
    isError: false,
  }),
}));

vi.mock("@/lib/config/public-config", () => ({
  tryGetPublicStrategistApiBaseUrl: () => ({ ok: true, baseUrl: "http://127.0.0.1:8000" }),
}));

vi.mock("@/hooks/useTerminalPageBind", () => ({ useTerminalPageBind: () => {} }));

vi.mock("@/lib/terminal/cockpit-context", () => ({
  useTerminalCockpit: () => ({ openInspector: vi.fn() }),
}));

describe("ResearchOsPage", () => {
  it("renders degraded rail and promotion recommendation without tokens", () => {
    const { container } = render(<ResearchOsPage />);
    expect(screen.getAllByText(/Research OS/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/DEGRADED/i)).toBeTruthy();
    expect(screen.getAllByText(/DO_NOT_PROMOTE/i).length).toBeGreaterThan(0);
    expect(container.textContent?.includes("STRATEGY_VALIDATOR_API_TOKEN")).toBe(false);
  });

  it("renders provider PENDING_KEY and artifact scan copy", () => {
    render(<ResearchOsPage />);
    expect(screen.getAllByText(/PENDING_KEY/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Artifact roots/i).length).toBeGreaterThan(0);
  });

  it("renders provider-backed paper loop pane", () => {
    render(<ResearchOsPage />);
    expect(screen.getAllByText(/Provider-backed paper loop/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/provider_paper_loop_manifest/i).length).toBeGreaterThan(0);
  });
});
