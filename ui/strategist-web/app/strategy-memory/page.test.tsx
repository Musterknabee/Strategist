/** @vitest-environment jsdom */

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import StrategyMemoryPage from "./page";

vi.mock("@/hooks/useUiStrategyMemory", () => ({
  useUiStrategyMemoryLatest: () => ({
    data: {
      schema_version: "ui_strategy_memory/v1",
      generated_at_utc: "2026-05-01T00:00:00+00:00",
      degraded: [],
      scan_root: "/tmp/artifacts/strategy_memory",
      latest: {
        active_count: 1,
        killed_count: 1,
        rejected_count: 0,
        duplicate_variant_count: 1,
        family_count: 1,
        index_sha256: "abc123",
        top_failure_reasons: { ROBUSTNESS: 1 },
        recent_graveyard_entries: [{ strategy_id: "bad-1", kill_reason: "ROBUSTNESS" }],
        duplicate_variant_warnings: [{ strategy_id: "dup-2", similar_strategy_id: "dup-1" }],
        memory_records: [
          { strategy_id: "mom-spy", family_id: "momentum:SPY", status: "ACTIVE_RESEARCH", strategy_type: "momentum", universe: "SPY", data_plane: "PROVIDER_SNAPSHOT", failure_reasons: [], record_sha256: "ffff" },
        ],
      },
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

describe("StrategyMemoryPage", () => {
  it("renders memory, graveyard, duplicate warnings, and no token copy", () => {
    const { container } = render(<StrategyMemoryPage />);
    expect(screen.getAllByText(/Strategy Memory/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Candidate graveyard/i)).toBeTruthy();
    expect(screen.getAllByText(/Duplicate warnings/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/mom-spy/i)).toBeTruthy();
    expect(container.textContent?.includes("STRATEGY_VALIDATOR_API_TOKEN")).toBe(false);
  });
});
