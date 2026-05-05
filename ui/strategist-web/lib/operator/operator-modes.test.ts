import { describe, expect, it } from "vitest";
import {
  COCKPIT_POST_GRID_SECTION_ORDER,
  deriveOperatorModeNextFocusLines,
  getPostGridSectionOrder,
  modeShowsOperatorCommandPane,
  OPERATOR_MODE_IDS,
} from "./operator-modes";

describe("operator modes registry", () => {
  it("lists all eight modes", () => {
    expect(OPERATOR_MODE_IDS).toHaveLength(8);
    expect(new Set(OPERATOR_MODE_IDS).size).toBe(8);
  });

  it("DAILY_OPS preserves default post-grid document order", () => {
    expect(getPostGridSectionOrder("DAILY_OPS")).toEqual(COCKPIT_POST_GRID_SECTION_ORDER);
  });

  it("FIRST_RUN moves setup panes before topology", () => {
    const o = getPostGridSectionOrder("FIRST_RUN");
    expect(o[0]).toBe("first_run");
    expect(o[1]).toBe("provider_setup");
    expect(o.indexOf("topology")).toBeLessThan(o.indexOf("release_control"));
  });

  it("SYSTEM_TOPOLOGY prioritizes topology section", () => {
    expect(getPostGridSectionOrder("SYSTEM_TOPOLOGY")[0]).toBe("topology");
  });

  it("modeShowsOperatorCommandPane matches safety classification", () => {
    expect(modeShowsOperatorCommandPane("DAILY_OPS")).toBe(true);
    expect(modeShowsOperatorCommandPane("RELEASE_CONTROL")).toBe(true);
    expect(modeShowsOperatorCommandPane("INCIDENT_RESPONSE")).toBe(true);
    expect(modeShowsOperatorCommandPane("FIRST_RUN")).toBe(false);
    expect(modeShowsOperatorCommandPane("SYSTEM_TOPOLOGY")).toBe(false);
  });

  it("deriveOperatorModeNextFocusLines uses hook-derived labels only", () => {
    const lines = deriveOperatorModeNextFocusLines("DAILY_OPS", {
      readyStatus: "READY",
      anyHookError: false,
      deploymentReadinessFailed: false,
      deploymentBlockerCodes: [],
      deploymentWarningCodes: [],
      cockpitDeploymentStatus: "UNKNOWN",
      operatorHealthFailed: false,
      researchLifecycleFailed: false,
      releaseControlFailed: false,
      remediationFailed: false,
      paperCapitalFailed: false,
      auditForensicFailed: false,
      topologyContractUnknown: false,
      chainIntegrityLabel: "CHAIN_OK",
    });
    expect(lines.length).toBeGreaterThan(0);
    expect(lines.some((l) => l.includes("Readiness status"))).toBe(true);
    expect(lines.some((l) => l.includes("Deployment evidence label: UNKNOWN"))).toBe(true);
  });
});
