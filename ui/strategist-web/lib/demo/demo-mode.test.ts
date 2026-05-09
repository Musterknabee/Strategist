import { describe, expect, it } from "vitest";
import { demoReadPlanePaths, getDemoCoverageReport, getDemoReadPlanePayload } from "./demo-mode";

const required = [
  "/ui/facade",
  "/healthz",
  "/readyz",
  "/ui/runtime",
  "/ui/evidence",
  "/ui/evidence-chain",
  "/ui/packs/workbench",
  "/ui/packs/detail",
  "/ui/operator-actions",
  "/ui/workboard",
  "/ui/provider-health",
  "/ui/provider-setup",
  "/ui/paper-execution",
  "/ui/research-os/status",
  "/ui/research-os/release-readiness/latest",
  "/ui/research-os/handoff/latest",
  "/ui/research-os/handoff-signoff/latest",
  "/ui/strategy-batches/latest",
  "/ui/backtest-forensics/latest",
  "/ui/strategy-intake/latest",
  "/ui/strategy-thesis/latest",
  "/ui/strategy-memory/latest",
  "/ui/strategy-graveyard/latest",
];

describe("demo read-plane registry", () => {
  it("covers required cockpit preview surfaces", () => {
    expect(demoReadPlanePaths).toEqual(expect.arrayContaining(required));
  });

  it("marks payloads as demo-only and never deployment-approved", () => {
    for (const path of required) {
      const payload = getDemoReadPlanePayload(path);
      expect(payload?.demo_only).toBe(true);
      expect(JSON.stringify(payload).toUpperCase()).toContain("DEMO");
      expect(JSON.stringify(payload).toUpperCase()).not.toContain("DEPLOYMENT_APPROVED\":TRUE");
    }
  });

  it("does not contain secret-looking material", () => {
    const blob = JSON.stringify(required.map((path) => getDemoReadPlanePayload(path)));
    expect(blob).not.toMatch(/PK[A-Z0-9]{10,}/);
    expect(blob).not.toMatch(/-----BEGIN [A-Z ]*PRIVATE KEY-----/);
    expect(blob).not.toMatch(/(?:token|secret|password)["']?\s*:\s*["'][A-Za-z0-9]{24,}/i);
  });

  it("reports contract coverage without claiming approval authority", () => {
    const report = getDemoCoverageReport();
    expect(report.demo_only).toBe(true);
    expect(report.safety).toMatchObject({
      mutations_disabled: true,
      real_readiness_claimed: false,
      deployment_approval_claimed: false,
      live_execution_authority: false,
    });
  });
});
