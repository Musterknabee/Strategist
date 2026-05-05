// @vitest-environment jsdom

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { EvidenceProvenanceBar } from "./EvidenceProvenanceBar";
import { OverviewPane } from "./OverviewPane";
import { inspectBody } from "./cockpit-utils";

describe("EvidenceProvenanceBar", () => {
  it("shows PENDING and UNKNOWN fallbacks when fields are absent", () => {
    render(
      <EvidenceProvenanceBar
        sourceLabel="READ · test"
        openInspector={() => {}}
        inspectorPayload={{ title: "T", subtitle: "S", body: null, rawJson: {} }}
      />,
    );
    expect(screen.getByTestId("evidence-provenance-bar")).toBeTruthy();
    expect(screen.getAllByText("PENDING").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("UNKNOWN").length).toBeGreaterThanOrEqual(1);
  });

  it("renders digest prefix and copy when digestFull is set", () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText } });
    const setLastDigest = vi.fn();
    render(
      <EvidenceProvenanceBar
        sourceLabel="READ · /ui/operator-actions"
        digestPreview="deadbeef00000000"
        digestFull="deadbeef00000000112233445566778899aabbccddeeff"
        trustStatus="CHAIN_OK"
        blockerCount={2}
        warningCount={1}
        openInspector={() => {}}
        inspectorPayload={{ title: "T", subtitle: "S", body: null, rawJson: {} }}
        setLastDigest={setLastDigest}
      />,
    );
    expect(screen.getByText("deadbeef00000000")).toBeTruthy();
    fireEvent.click(screen.getByTitle("Copy full digest"));
    expect(writeText).toHaveBeenCalledWith("deadbeef00000000112233445566778899aabbccddeeff");
    expect(setLastDigest).toHaveBeenCalledWith("deadbeef0000000011");
    expect(screen.getByText("2")).toBeTruthy();
    expect(screen.getByText("1")).toBeTruthy();
    vi.unstubAllGlobals();
  });

  it("shows VERIFY when projectionSnapshotVerified is boolean", () => {
    render(
      <EvidenceProvenanceBar
        sourceLabel="READ · /ui/evidence"
        projectionSnapshotVerified={false}
        openInspector={() => {}}
        inspectorPayload={{ title: "T", subtitle: "S", body: null, rawJson: {} }}
      />,
    );
    expect(screen.getByText("UNVERIFIED")).toBeTruthy();
  });
});

describe("OverviewPane without backend payloads", () => {
  it("still renders tiles and provenance strip", () => {
    const openInspector = vi.fn();
    render(
      <OverviewPane
        overviewTiles={[
          { label: "Health", status: "UNKNOWN", hint: "no data", raw: null },
        ]}
        provenance={{
          sourceLabel: "AGGREGATE · read-plane",
        }}
        inspectorPayload={{
          title: "System Summary",
          subtitle: "aggregate",
          body: inspectBody({ status: "UNKNOWN", summary: "empty" }),
          rawJson: {},
        }}
        openInspector={openInspector}
        setLastDigest={() => {}}
      />,
    );
    expect(screen.getByText("Overview")).toBeTruthy();
    expect(screen.getByTestId("overview-evidence-provenance")).toBeTruthy();
    expect(screen.getByText("Health")).toBeTruthy();
  });
});
