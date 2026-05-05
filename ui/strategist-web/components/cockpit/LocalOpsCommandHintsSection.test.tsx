/** @vitest-environment jsdom */

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LocalOpsCommandHintsSection } from "./LocalOpsCommandHintsSection";

afterEach(() => {
  cleanup();
});

describe("LocalOpsCommandHintsSection", () => {
  it("renders production-sensitive warning and never runs shell", () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText } });
    render(
      <LocalOpsCommandHintsSection
        commandIds={["loc_st_acceptance"]}
        testIdPrefix="test-local-ops-hints"
        intro="Intro line"
      />,
    );
    expect(screen.getByTestId("test-local-ops-hints-browser-note").textContent).toContain("Browser does not execute");
    expect(screen.getByText(/Intro line/)).toBeTruthy();
    expect(screen.getByText(/Reads deployment\.env/)).toBeTruthy();
    fireEvent.click(screen.getByTestId("test-local-ops-hints-copy-loc_st_acceptance"));
    expect(writeText).toHaveBeenCalledTimes(1);
    expect(writeText.mock.calls[0][0]).toContain("strategy-validator-single-tenant-acceptance");
    vi.unstubAllGlobals();
  });
});
