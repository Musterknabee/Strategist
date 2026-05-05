/** @vitest-environment jsdom */

import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DemoModeBanner } from "@/components/demo/DemoModeBanner";
import { isStrategistDemoModeEnabled } from "@/lib/config/public-config";
import { demoReadPlanePaths, getDemoCoverageReport, getDemoReadPlanePayload } from "@/lib/demo/demo-mode";

const here = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(here, "..");

describe("cockpit acceptance pack: demo and evidence honesty", () => {
  it("keeps demo mode opt-in with visible synthetic banner copy", () => {
    delete process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE;
    expect(isStrategistDemoModeEnabled()).toBe(false);
    render(<DemoModeBanner />);
    expect(screen.queryByText("DEMO MODE")).toBeNull();

    process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE = "true";
    render(<DemoModeBanner />);
    expect(screen.getByText("DEMO MODE")).toBeTruthy();
    expect(screen.getByText("No real backend evidence")).toBeTruthy();
    expect(screen.getByText("No deployment approval")).toBeTruthy();
    expect(screen.getByText("Synthetic data only")).toBeTruthy();
    delete process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE;
  });

  it("keeps demo payloads synthetic, secret-free, and non-approving", () => {
    const payloads = demoReadPlanePaths.map((path) => getDemoReadPlanePayload(path));
    const blob = JSON.stringify(payloads).toUpperCase();

    expect(blob).toContain("DEMO_DATA_NOT_REAL");
    expect(blob).toContain("NO_DEPLOYMENT_APPROVAL");
    expect(blob).not.toMatch(/PK[A-Z0-9]{10,}/);
    expect(blob).not.toMatch(/-----BEGIN [A-Z ]*PRIVATE KEY-----/);
    expect(blob).not.toMatch(/TOKEN["']?\s*:\s*["'][A-Z0-9._-]{24,}/);
    expect(blob).not.toContain('"DEPLOYMENT_APPROVED":TRUE');
    expect(blob).not.toContain('"SIGNOFF_COMPLETE"');
    expect(blob).not.toContain('"LIVE_TRADING":TRUE');

    const coverage = getDemoCoverageReport();
    expect(coverage.safety).toMatchObject({
      mutations_disabled: true,
      real_readiness_claimed: false,
      deployment_approval_claimed: false,
      live_execution_authority: false,
    });
  });

  it("preserves production-honest copy in release, evidence, and first-run panes", () => {
    const files = [
      "components/cockpit/EvidenceRunbookPane.tsx",
      "components/cockpit/ReleaseControlPane.tsx",
      "components/cockpit/SingleTenantFirstRunWizard.tsx",
      "lib/operator/evidence-packet-model.ts",
      "lib/operator/release-control-model.ts",
      "lib/operator/execution-firewall-model.ts",
    ];
    const blob = files.map((file) => readFileSync(join(webRoot, file), "utf8")).join("\n").toLowerCase();

    expect(blob).toContain("not deployment approval");
    expect(blob).toContain("no shell execution");
    expect(blob).toContain("no live");
    expect(blob).toContain("does not infer");
  });
});
