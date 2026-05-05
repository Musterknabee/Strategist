// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { getOperatorModeDefinition } from "@/lib/operator/operator-modes";
import { OperatorModeSwitchboard } from "./OperatorModeSwitchboard";

afterEach(() => cleanup());

describe("OperatorModeSwitchboard", () => {
  it("renders all mode chips and command banner when COMMAND_CAPABLE", () => {
    const onChange = vi.fn();
    render(
      <OperatorModeSwitchboard
        mode="DAILY_OPS"
        onChange={onChange}
        definition={getOperatorModeDefinition("DAILY_OPS")}
        nextFocusLines={["Line a", "Line b"]}
        postGridOrderPreview={["topology", "operator_health"]}
      />,
    );
    expect(screen.getByTestId("cockpit-mode-switchboard")).toBeTruthy();
    expect(screen.getByTestId("cockpit-mode-select-FIRST_RUN")).toBeTruthy();
    expect(screen.getByTestId("cockpit-mode-select-SYSTEM_TOPOLOGY")).toBeTruthy();
    expect(screen.getByTestId("cockpit-mode-command-banner")).toBeTruthy();
    fireEvent.click(screen.getByTestId("cockpit-mode-select-RELEASE_CONTROL"));
    expect(onChange).toHaveBeenCalledWith("RELEASE_CONTROL");
  });

  it("shows read-only banner for READ_PLANE_ONLY modes", () => {
    render(
      <OperatorModeSwitchboard
        mode="FIRST_RUN"
        onChange={vi.fn()}
        definition={getOperatorModeDefinition("FIRST_RUN")}
        nextFocusLines={["PENDING"]}
        postGridOrderPreview={["first_run"]}
      />,
    );
    expect(screen.getByTestId("cockpit-mode-readonly-banner")).toBeTruthy();
    expect(screen.queryByTestId("cockpit-mode-command-banner")).toBeNull();
  });
});
