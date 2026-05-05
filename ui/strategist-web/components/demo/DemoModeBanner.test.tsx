/** @vitest-environment jsdom */

import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { DemoModeBanner } from "./DemoModeBanner";

describe("DemoModeBanner", () => {
  afterEach(() => {
    delete process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE;
  });

  it("is hidden unless demo mode is explicitly enabled", () => {
    render(<DemoModeBanner />);
    expect(screen.queryByText("DEMO MODE")).toBeNull();
  });

  it("renders persistent safety copy when enabled", () => {
    process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE = "true";
    render(<DemoModeBanner />);
    expect(screen.getByText("DEMO MODE")).toBeTruthy();
    expect(screen.getByText("Synthetic read-plane data only")).toBeTruthy();
    expect(screen.getByText("No backend readiness claim")).toBeTruthy();
    expect(screen.getByText("No provider credentials")).toBeTruthy();
    expect(screen.getByText("No deployment approval")).toBeTruthy();
    expect(screen.getByText("No operator signoff")).toBeTruthy();
    expect(screen.getByText("No live trading or broker orders")).toBeTruthy();
    expect(screen.getByText("No profitability claim")).toBeTruthy();
  });
});
