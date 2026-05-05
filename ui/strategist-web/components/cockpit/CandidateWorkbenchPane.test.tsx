/** @vitest-environment jsdom */

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CandidateWorkbenchPane } from "./CandidateWorkbenchPane";

afterEach(() => cleanup());

describe("CandidateWorkbenchPane", () => {
  it("renders empty state and paper-only disclaimer", () => {
    render(
      <CandidateWorkbenchPane
        strategyMemoryLatest={null}
        strategyGraveyardLatest={null}
        backtestForensicsLatest={null}
        paperTrackingLatest={null}
        providerSetup={null}
        providerHealth={null}
        evidenceChain={null}
        openInspector={vi.fn()}
        onOpenMode={vi.fn()}
      />,
    );
    expect(screen.getByTestId("cockpit-candidate-workbench")).toBeTruthy();
    expect(screen.getByText(/Paper\/research only/)).toBeTruthy();
    expect(screen.getByTestId("candidate-workbench-empty").textContent).toMatch(/UNKNOWN .* no candidates/i);
  });

  it("filters to blocked rows and keeps details accessible", () => {
    const onOpenMode = vi.fn();
    render(
      <CandidateWorkbenchPane
        strategyMemoryLatest={{ latest: { duplicate_variant_count: 0, memory_records: [{ strategy_id: "strat-x" }] } }}
        strategyGraveyardLatest={null}
        backtestForensicsLatest={null}
        paperTrackingLatest={{
          latest: {
            tracking_id: "trk-x",
            manifest: { candidate: { strategy_id: "strat-x" } },
            lifecycle_blockers: ["BLOCKED"],
            scorecard: { warning_count: 0 },
          },
        }}
        providerSetup={null}
        providerHealth={null}
        evidenceChain={{ timeline: { entries: [] }, degraded: [], summary: { chain_issue_count_total: 0 } }}
        openInspector={vi.fn()}
        onOpenMode={onOpenMode}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /show blocked candidates/i }));
    expect(screen.getByText(/strat-x/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Research Review" }));
    expect(onOpenMode).toHaveBeenCalledWith("RESEARCH_REVIEW");
  });
});
