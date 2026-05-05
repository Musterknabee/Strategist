/** @vitest-environment jsdom */

import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { OperatorModeSwitchboard } from "@/components/cockpit/OperatorModeSwitchboard";
import {
  getOperatorModeDefinition,
  getPostGridSectionOrder,
  modeShowsOperatorCommandPane,
  OPERATOR_MODE_IDS,
  type OperatorModeId,
} from "@/lib/operator/operator-modes";

const EXPECTED_MODES: OperatorModeId[] = [
  "DAILY_OPS",
  "FIRST_RUN",
  "RESEARCH_REVIEW",
  "RELEASE_CONTROL",
  "INCIDENT_RESPONSE",
  "FORENSIC_AUDIT",
  "CAPITAL_FIREWALL",
  "SYSTEM_TOPOLOGY",
];

describe("cockpit acceptance pack: mode renderability", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("registers the complete operator mode inventory", () => {
    expect(OPERATOR_MODE_IDS).toEqual(EXPECTED_MODES);
  });

  it.each(EXPECTED_MODES)("renders %s mode switchboard without mutation/network side effects", (mode) => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const onChange = vi.fn();
    const definition = getOperatorModeDefinition(mode);

    render(
      <OperatorModeSwitchboard
        mode={mode}
        onChange={onChange}
        definition={definition}
        nextFocusLines={["PENDING - acceptance render proof only"]}
        postGridOrderPreview={getPostGridSectionOrder(mode)}
      />,
    );

    expect(screen.getByTestId("cockpit-mode-current-label").textContent).toBe(definition.label);
    expect(screen.getByTestId("cockpit-mode-primary-panes").textContent).toBeTruthy();
    expect(screen.getByTestId("cockpit-mode-secondary-panes").textContent).toBeTruthy();

    if (modeShowsOperatorCommandPane(mode)) {
      const commandBanner = screen.getByTestId("cockpit-mode-command-banner").textContent ?? "";
      expect(commandBanner).toContain("Command-capable mode");
      expect(commandBanner).toMatch(/token-gated|authenticated|trusted workstations/);
    } else {
      expect(screen.getByTestId("cockpit-mode-readonly-banner").textContent).toContain("no shell execution");
    }

    for (const id of EXPECTED_MODES) {
      fireEvent.click(screen.getByTestId(`cockpit-mode-select-${id}`));
    }

    expect(onChange).toHaveBeenCalledTimes(EXPECTED_MODES.length);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("keeps every mode backed by a transparent post-grid pane order", () => {
    for (const mode of EXPECTED_MODES) {
      const order = getPostGridSectionOrder(mode);
      expect(order.length).toBeGreaterThan(5);
      expect(new Set(order).size).toBe(order.length);
      expect(order).toContain("operator_command");
      expect(order).toContain("evidence_runbook");
    }
  });
});
