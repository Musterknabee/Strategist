// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PaperExecutionEvidenceDrilldownPane } from "./PaperExecutionEvidenceDrilldownPane";
import { ResearchOsEvidenceDrilldownPane } from "./ResearchOsEvidenceDrilldownPane";
import { buildPaperExecutionEvidenceRows, buildResearchOsEvidenceRows } from "@/lib/operator/cockpit-evidence-drilldown-rows";
import { inspectBody } from "./cockpit-utils";

afterEach(() => cleanup());

describe("ResearchOsEvidenceDrilldownPane", () => {
  it("renders UNKNOWN/PENDING when rows are empty-shaped", () => {
    const rows = buildResearchOsEvidenceRows(null);
    const openInspector = vi.fn();
    render(
      <ResearchOsEvidenceDrilldownPane
        rows={rows}
        queryFailed={false}
        selectedKey={null}
        setSelectedKey={() => {}}
        openInspector={openInspector}
        setLastDigest={() => {}}
        provenance={{ sourceLabel: "READ · test" }}
        inspectorPayload={{ title: "ROS", subtitle: "s", body: inspectBody({ status: "OK", summary: "x" }), rawJson: {} }}
      />,
    );
    expect(screen.getByTestId("cockpit-research-os-drilldown")).toBeTruthy();
    expect(screen.getAllByText("UNKNOWN").length).toBeGreaterThan(0);
  });

  it("opens inspector with row raw JSON on click", () => {
    const rows = buildResearchOsEvidenceRows({
      schema_version: "ui_research_os_status/v1",
      generated_at_utc: "2026-05-01T12:00:00Z",
      research_os_closure_latest: {
        status: "PRESENT",
        generated_at_utc: "2026-05-01T12:00:00Z",
        latest: { status: "COMPLETE", trust_banner: "TRUSTED", manifest_sha256: "ab".repeat(32), blockers: [], warnings: [] },
        degraded: [],
      },
      research_os_attestation_latest: { status: "NOT_PRESENT", degraded: [] },
      research_os_evidence_drift_latest: { status: "NOT_PRESENT", degraded: [] },
      research_os_policy_gate_latest: { status: "NOT_PRESENT", degraded: [] },
      research_os_release_readiness_latest: { status: "NOT_PRESENT", degraded: [] },
      research_os_exception_latest: { status: "NOT_PRESENT", degraded: [] },
      research_os_remediation_latest: { status: "NOT_PRESENT", degraded: [] },
    });
    const openInspector = vi.fn();
    render(
      <ResearchOsEvidenceDrilldownPane
        rows={rows}
        queryFailed={false}
        selectedKey={null}
        setSelectedKey={() => {}}
        openInspector={openInspector}
        setLastDigest={() => {}}
        provenance={{ sourceLabel: "READ · test" }}
        inspectorPayload={{ title: "ROS", subtitle: "s", body: inspectBody({ status: "OK", summary: "x" }), rawJson: {} }}
      />,
    );
    fireEvent.click(screen.getByText("Closure manifest"));
    expect(openInspector).toHaveBeenCalled();
    const arg = openInspector.mock.calls[0][0];
    expect(arg.rawJson).toBeTruthy();
  });
});

describe("PaperExecutionEvidenceDrilldownPane", () => {
  it("renders posture row with PAPER_ONLY when flags set", () => {
    const rows = buildPaperExecutionEvidenceRows({
      schema_version: "x",
      generated_at_utc: "2026-05-01T12:00:00Z",
      read_plane_only: true,
      no_live_trading: true,
      no_browser_orders: true,
      execution_authority: "NOT_BLOCKED",
      summary: {
        broker_policy_status: "PAPER_READY",
        paper_submission_capability: "CLI_ONLY",
        submission_guard_blocker_count: 0,
        evidence_bundle_blocker_count: 0,
        timeline_blocker_count: 0,
        evidence_freshness_blocker_count: 0,
        timeline_warning_count: 0,
        position_reconciliation_warning_count: 0,
      },
    });
    render(
      <PaperExecutionEvidenceDrilldownPane
        rows={rows}
        queryFailed={false}
        selectedKey={null}
        setSelectedKey={() => {}}
        openInspector={vi.fn()}
        setLastDigest={() => {}}
        provenance={{ sourceLabel: "READ · paper" }}
        inspectorPayload={{ title: "PE", subtitle: "s", body: inspectBody({ status: "OK", summary: "x" }), rawJson: {} }}
      />,
    );
    expect(screen.getByTestId("cockpit-paper-execution-drilldown")).toBeTruthy();
    expect(screen.getByText(/PAPER_ONLY/)).toBeTruthy();
  });
});
