/** @vitest-environment jsdom */

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ThesisPage from "./page";

vi.mock("@/hooks/useUiStrategyThesis", () => ({
  useUiStrategyThesisGenerationLatest: () => ({
    data: {
      schema_version: "ui_strategy_thesis_generation/v1",
      degraded: [],
      latest_generation: {
        run_id: "run-1",
        generated_count: 1,
        evaluated_count: 1,
        report_sha256: "def456",
        generated_theses: [{ strategy_id: "mom-spy", support_status: "SUPPORTED" }],
      },
    },
    isLoading: false,
    isError: false,
  }),
  useUiStrategyThesisLatest: () => ({
    data: {
      schema_version: "ui_strategy_thesis/v1",
      degraded: [],
      latest: {
        strategy_id: "mom-spy",
        thesis_id: "thesis-1",
        support_status: "FALSIFIED",
        contradictions: ["FALSIFICATION_TRIGGERED:max-dd:max_drawdown"],
        missing_evidence: [],
        evaluation_sha256: "abc123",
      },
    },
    isLoading: false,
    isError: false,
  }),
}));
vi.mock("@/lib/config/public-config", () => ({ tryGetPublicStrategistApiBaseUrl: () => ({ ok: true, baseUrl: "http://127.0.0.1:8000" }) }));
vi.mock("@/hooks/useTerminalPageBind", () => ({ useTerminalPageBind: () => {} }));
vi.mock("@/lib/terminal/cockpit-context", () => ({ useTerminalCockpit: () => ({ openInspector: vi.fn() }) }));

describe("ThesisPage", () => {
  it("renders thesis falsification status and no token copy", () => {
    const { container } = render(<ThesisPage />);
    expect(screen.getByText(/Strategy Thesis/i)).toBeTruthy();
    expect(screen.getAllByText(/FALSIFIED/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/FALSIFICATION_TRIGGERED/i)).toBeTruthy();
    expect(container.textContent?.includes("STRATEGY_VALIDATOR_API_TOKEN")).toBe(false);
  });
});
