/** @vitest-environment jsdom */

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ProviderSetupReadinessPane } from "./ProviderSetupReadinessPane";
import type { UiProviderSetupConsolePayload } from "@/lib/api/types";

afterEach(() => cleanup());

function payload(overrides: Partial<UiProviderSetupConsolePayload> = {}): UiProviderSetupConsolePayload {
  return {
    schema_version: "ui_provider_setup_console/v1",
    generated_at_utc: "2026-05-04T20:00:00Z",
    read_plane_only: true,
    mutation_authority: "none",
    execution_authority: "none",
    no_network_calls: true,
    no_secret_values: true,
    freshness_max_age_seconds: 86400,
    samples_manifest_path: "docs/artifacts/provider-samples.json",
    samples_manifest_digest_prefix: "abc123",
    execution_workflow_blockers: ["policy_blocker"],
    summary: {
      provider_count: 1,
      ready_count: 0,
      blocked_count: 1,
      action_required_count: 0,
      stale_count: 0,
      not_checked_count: 1,
      missing_secret_count: 1,
      public_no_signup_count: 0,
      keyed_provider_count: 1,
      pit_strong_count: 0,
    },
    entries: [
      {
        provider_id: "alpaca",
        display_name: "Alpaca",
        category: "broker",
        research_role: "paper broker",
        access_type: "BROKER_ACCOUNT_REQUIRED",
        trust_level: "BROKER_EXECUTION",
        pit_suitability: "EXECUTION_ONLY",
        recommended_priority: 1,
        expected_env_vars: ["ALPACA_API_KEY", "ALPACA_API_SECRET"],
        requires_secret: true,
        configured: false,
        reachable: false,
        classified_status: "NOT_CHECKED",
        setup_status: "MISSING_OPTIONAL_SECRET",
        readiness_tier: "BLOCKED",
        freshness_class: "NOT_CHECKED",
        freshness_age_seconds: null,
        freshness_max_age_seconds: 86400,
        warnings: ["warn-a"],
        blockers: ["block-a"],
        remediation: ["Do x"],
        sample_digest_prefix: "deadbeef",
        evidence_reference: "docs/artifacts/provider-samples.json#provider_id=alpaca",
        may_gate_live_promotion: true,
        unsafe_as_promotion_authority_without_license: true,
      },
    ],
    ...overrides,
  };
}

describe("ProviderSetupReadinessPane", () => {
  it("renders unknown/pending-safe empty state", () => {
    render(<ProviderSetupReadinessPane providerSetupData={null} providerHealthData={null} openInspector={vi.fn()} />);
    expect(screen.getByTestId("cockpit-provider-setup-readiness")).toBeTruthy();
    expect(screen.getByText(/provider setup unavailable/i)).toBeTruthy();
  });

  it("renders expected env names and copy placeholders only", () => {
    const openInspector = vi.fn();
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText } });
    render(<ProviderSetupReadinessPane providerSetupData={payload()} providerHealthData={{}} openInspector={openInspector} />);
    fireEvent.click(screen.getAllByText("Alpaca")[1]);
    expect(openInspector).toHaveBeenCalled();
    const raw = JSON.stringify(openInspector.mock.calls[0][0].rawJson);
    expect(raw).toContain("ALPACA_API_KEY");
    expect(raw).not.toContain("sk-live");
    // copy button lives inside inspector body; assert placeholder string in payload from model via rawJson
    expect(raw).toContain("env_hint_lines");
    expect(raw).toContain("<set-in-gitignored-env-file>");
    vi.unstubAllGlobals();
  });

  it("shows blockers/warnings and PIT + safety semantics", () => {
    const openInspector = vi.fn();
    render(<ProviderSetupReadinessPane providerSetupData={payload()} providerHealthData={{}} openInspector={openInspector} />);
    fireEvent.click(screen.getAllByText("Alpaca")[1]);
    const raw = openInspector.mock.calls[0][0].rawJson as Record<string, unknown>;
    expect(raw.pit_suitability).toBe("EXECUTION_ONLY");
    expect(raw.may_gate_live_promotion).toBe(true);
    expect(raw.unsafe_as_promotion_authority_without_license).toBe(true);
    expect((raw.warnings as string[])[0]).toBe("warn-a");
    expect((raw.blockers as string[])[0]).toBe("block-a");
  });

  it("does not call mutation endpoints (no fetch) on render/click", () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    render(<ProviderSetupReadinessPane providerSetupData={payload()} providerHealthData={{}} openInspector={vi.fn()} />);
    fireEvent.click(screen.getAllByText("Alpaca")[1]);
    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });
});
