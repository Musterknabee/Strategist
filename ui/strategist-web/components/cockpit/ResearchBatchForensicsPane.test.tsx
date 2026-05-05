// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ResearchBatchForensicsPane } from "./ResearchBatchForensicsPane";

afterEach(() => cleanup());

describe("ResearchBatchForensicsPane", () => {
  it("renders with missing backend data as UNKNOWN/PENDING-safe", () => {
    render(
      <ResearchBatchForensicsPane
        strategyBatchLatest={null}
        strategyBatchesList={null}
        backtestForensicsLatest={null}
        paperTrackingLatest={null}
        strategyGraveyardLatest={null}
        strategyMemoryLatest={null}
        strategyThesisLatest={null}
        shadowBookLatest={null}
        openInspector={vi.fn()}
      />,
    );
    expect(screen.getByTestId("cockpit-research-batch-forensics")).toBeTruthy();
    expect(screen.getAllByText("PENDING").length).toBeGreaterThan(0);
  });

  it("shows digest prefixes and opens inspector on row click", () => {
    const openInspector = vi.fn();
    render(
      <ResearchBatchForensicsPane
        strategyBatchLatest={{
          generated_at_utc: "2026-05-01T10:00:00Z",
          latest: {
            run_id: "run-42",
            ok: false,
            blocked_count: 1,
            failed_count: 1,
            top_candidate: "STRAT-X",
            batch_sha256: "0123456789abcdef0123456789abcdef",
          },
        }}
        strategyBatchesList={{ batches: [] }}
        backtestForensicsLatest={{ summary: {}, degraded: [] }}
        paperTrackingLatest={{ latest: { tracking_id: "trk-1", lifecycle_state: "PAPER_ONLY" } }}
        strategyGraveyardLatest={{ summary: { hard_blocked_count: 0, operator_review_count: 0 } }}
        strategyMemoryLatest={{ latest: { index_sha256: "ab".repeat(32), duplicate_variant_count: 0, killed_count: 0 } }}
        strategyThesisLatest={{}}
        shadowBookLatest={{}}
        openInspector={openInspector}
      />,
    );
    expect(screen.getByText(/0123456789ab\.\.\./)).toBeTruthy();
    fireEvent.click(screen.getAllByText("Latest Batch")[1]);
    expect(openInspector).toHaveBeenCalled();
  });

  it("does not call mutation endpoints", () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    render(
      <ResearchBatchForensicsPane
        strategyBatchLatest={null}
        strategyBatchesList={null}
        backtestForensicsLatest={null}
        paperTrackingLatest={null}
        strategyGraveyardLatest={null}
        strategyMemoryLatest={null}
        strategyThesisLatest={null}
        shadowBookLatest={null}
        openInspector={vi.fn()}
      />,
    );
    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });
});
