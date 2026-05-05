import { describe, expect, it } from "vitest";
import { buildProviderReadinessModel, providerReadinessPaneStatus } from "./provider-readiness-model";
import type { UiProviderSetupConsolePayload } from "@/lib/api/types";

function samplePayload(): UiProviderSetupConsolePayload {
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
    samples_manifest_digest_prefix: "abc123def456",
    execution_workflow_blockers: ["alpaca_live_without_personal_live_approval"],
    summary: {
      provider_count: 2,
      ready_count: 1,
      blocked_count: 1,
      action_required_count: 0,
      stale_count: 1,
      not_checked_count: 0,
      missing_secret_count: 1,
      public_no_signup_count: 0,
      keyed_provider_count: 2,
      pit_strong_count: 1,
    },
    entries: [
      {
        provider_id: "alpha",
        display_name: "Alpha Data",
        category: "market_data",
        research_role: "market data",
        access_type: "API_KEY_REQUIRED",
        trust_level: "REVIEWED",
        pit_suitability: "STRONG_PIT_SOURCE",
        recommended_priority: 10,
        expected_env_vars: ["ALPHA_API_KEY"],
        requires_secret: true,
        configured: false,
        reachable: false,
        classified_status: "NOT_CHECKED",
        setup_status: "MISSING_OPTIONAL_SECRET",
        readiness_tier: "ACTION_REQUIRED",
        freshness_class: "NOT_CHECKED",
        freshness_age_seconds: null,
        freshness_max_age_seconds: 86400,
        warnings: ["optional_provider_not_configured"],
        blockers: [],
        remediation: ["Add key"],
        may_gate_live_promotion: true,
        unsafe_as_promotion_authority_without_license: true,
      },
      {
        provider_id: "beta",
        display_name: "Beta Data",
        category: "macro",
        research_role: "macro",
        access_type: "API_KEY_REQUIRED",
        trust_level: "PROVISIONAL",
        pit_suitability: "LIMITED_PIT_SOURCE",
        recommended_priority: 20,
        expected_env_vars: ["BETA_TOKEN"],
        requires_secret: true,
        configured: true,
        reachable: true,
        classified_status: "OK",
        setup_status: "READY",
        readiness_tier: "READY",
        freshness_class: "FRESH",
        freshness_age_seconds: 40,
        freshness_max_age_seconds: 86400,
        warnings: [],
        blockers: [],
        remediation: [],
        may_gate_live_promotion: false,
        unsafe_as_promotion_authority_without_license: false,
      },
    ],
  };
}

describe("provider readiness model", () => {
  it("builds rows with env hint placeholders only", () => {
    const model = buildProviderReadinessModel(samplePayload(), {});
    expect(model.rows[0].env_hint_lines[0]).toBe("ALPHA_API_KEY=<set-in-gitignored-env-file>");
    expect(model.rows[0].env_hint_lines.join(" ")).not.toContain("secret");
  });

  it("selects recommended next provider by urgency and priority", () => {
    const model = buildProviderReadinessModel(samplePayload(), {});
    expect(model.recommended_next_provider_id).toBe("alpha");
  });

  it("computes pane status from blocked/action-required counts", () => {
    const model = buildProviderReadinessModel(samplePayload(), {});
    expect(providerReadinessPaneStatus(model)).toBe("BLOCKED");
  });

  it("handles empty/missing data as UNKNOWN", () => {
    const model = buildProviderReadinessModel(null, null);
    expect(model.rows).toEqual([]);
    expect(providerReadinessPaneStatus(model)).toBe("UNKNOWN");
  });
});
