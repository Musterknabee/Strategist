/** @vitest-environment jsdom */

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuditForensicPane } from "./AuditForensicPane";

afterEach(() => cleanup());

describe("AuditForensicPane", () => {
  const openInspector = vi.fn();

  it("shows NO_BASELINE forensic block and filter narrows rows", () => {
    render(
      <AuditForensicPane
        evidenceChain={{
          schema_version: "ui_evidence_chain/v1",
          generated_at_utc: "2026-01-03T00:00:00Z",
          ok: true,
          degraded: [],
          timeline: {
            entries: [
              {
                stream_family: "decision_ledger",
                record_id: "r1",
                created_at_utc: "2026-01-03T00:00:01Z",
                event_type: "x",
                status: "READY",
                promotion_state: "READY",
                chained: true,
                issue_codes: [],
                event_hash: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
              },
            ],
          },
        }}
        operatorActions={null}
        evidence={null}
        releaseReadiness={null}
        handoff={null}
        handoffSignoff={null}
        reviewJournal={null}
        exportLatest={null}
        driftLatest={null}
        paperExecution={null}
        queryFailed={false}
        openInspector={openInspector}
      />,
    );
    expect(screen.getByTestId("cockpit-audit-forensic")).toBeTruthy();
    expect(screen.getByTestId("cockpit-audit-forensic-diff-promotion-tail").textContent).toContain("NO_BASELINE");
    fireEvent.click(screen.getByTestId("cockpit-audit-filter-PROMOTION_LEDGER"));
    expect(screen.getByText("decision_ledger")).toBeTruthy();
    fireEvent.click(screen.getByTestId("cockpit-audit-filter-RESEARCH_OS"));
    expect(screen.getByText(/no timeline entries for this filter/i)).toBeTruthy();
  });
});
