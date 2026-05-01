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
      gauntlet_latest: { batch_id: "b1", run_id: "r1", ok: true },
      paper_tracking_latest: { latest: { lifecycle_state: "PAPER_TRACKING", promotion_review_ready: false } },
      promotion_packet_latest: { recommendation: "DO_NOT_PROMOTE" },
      paper_broker_status: { policy_status: "PENDING_KEY" },
      compute_status: { research_compute_readiness: "CPU_FALLBACK_READY", gpu_probe: { gpu_available: false } },
      demo_manifest: { status: "NOT_PRESENT", artifact_path: "/x" },
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
    expect(screen.getByText(/Research OS/i)).toBeTruthy();
    expect(screen.getByText(/DEGRADED/i)).toBeTruthy();
    expect(screen.getByText(/DO_NOT_PROMOTE/i)).toBeTruthy();
    expect(container.textContent?.includes("STRATEGY_VALIDATOR_API_TOKEN")).toBe(false);
  });
});
