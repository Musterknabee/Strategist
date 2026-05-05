/** @vitest-environment jsdom */

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { EvidenceRunbookPane } from "./EvidenceRunbookPane";

afterEach(() => cleanup());

describe("EvidenceRunbookPane", () => {
  const openInspector = vi.fn();

  it("renders disclaimer and UNKNOWN posture without data", () => {
    render(
      <EvidenceRunbookPane
        facade={null}
        evidence={null}
        evidenceChain={null}
        operatorActions={null}
        releaseReadiness={null}
        handoff={null}
        handoffSignoff={null}
        reviewJournal={null}
        exportLatest={null}
        queryFailed={false}
        openInspector={openInspector}
      />,
    );
    expect(screen.getByTestId("cockpit-evidence-runbook")).toBeTruthy();
    expect(screen.getByTestId("cockpit-evidence-runbook-disclaimer").textContent).toContain("not deployment approval");
    expect(screen.getByText(/Clipboard only/)).toBeTruthy();
  });

  it("copy markdown uses clipboard only", () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText } });
    render(
      <EvidenceRunbookPane
        facade={null}
        evidence={{ schema_version: "ui_evidence_dashboard/v1", generated_at_utc: "2026-01-01T00:00:00Z", registry: {} }}
        evidenceChain={null}
        operatorActions={null}
        releaseReadiness={null}
        handoff={null}
        handoffSignoff={null}
        reviewJournal={null}
        exportLatest={null}
        queryFailed={false}
        openInspector={openInspector}
      />,
    );
    fireEvent.click(screen.getByTestId("cockpit-evidence-runbook-copy-markdown"));
    expect(writeText).toHaveBeenCalledTimes(1);
    expect(writeText.mock.calls[0][0]).toContain("# Strategist operator evidence runbook");
    vi.unstubAllGlobals();
  });
});
