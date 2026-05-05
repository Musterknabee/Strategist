import { describe, expect, it } from "vitest";
import {
  FIRST_RUN_CLI_HINTS,
  buildFirstRunDeploymentChecklist,
  firstRunTrustSummary,
  suggestNextFirstRunCommand,
  type FirstRunChecklistInput,
} from "./first-run-deployment-checklist";

function baseInput(overrides: Partial<FirstRunChecklistInput> = {}): FirstRunChecklistInput {
  return {
    deployment: {
      data: {
        checks: {
          environment_overrides_valid: true,
          private_key_material_absent: true,
          ledger_database_path_configured: true,
          ledger_path_resolved: true,
          schema_compatibility: true,
          ledger_backup_dir_configured: true,
          backup_root_writable: true,
        },
      },
      isLoading: false,
      isError: false,
    },
    readyz: { httpStatus: 200, body: { status: "READY", checks: { schema_current: true } }, isError: false, isLoading: false },
    healthz: { isError: false, isLoading: false, data: { ok: true } },
    livez: { httpStatus: 200, isError: false, isLoading: false },
    facade: {
      data: {
        schema_version: "ui_public_facade_inventory/v1",
        surface: "ui",
        frontend_expected_package: "ui/strategist-web",
        frontend_package_present: true,
        frontend_readiness_claimed: false,
        read_plane_only: true,
        mutation_route: "/ui/commands/{action}",
        routes: [],
      },
      isError: false,
    },
    mutationSafety: {
      runtime_mode: "DEV",
      authorization_mode: "NON_PRODUCTION_BYPASS",
      token_configured: false,
      mutation_routes_safe: true,
      detail_code: "NON_PRODUCTION_BYPASS",
    },
    cockpit: {
      deployment_status: "PASS",
      deployment_evidence_ok: true,
      operator_decision: "X",
      manual_operator_signoff_present: true,
      api_smoke_status: "PASS",
      api_smoke_ok: true,
      backup_restore_ok: true,
      ledger_integrity_ok: true,
      ci_local_verify_ok: true,
      frontend_readiness_status: "NOT_CLAIMED",
      evidence_generated_at_utc: "2026-01-01T00:00:00Z",
    },
    evidencePayload: {
      search_root: "/tmp/artifacts",
      registry: { projection_digest_sha256: "abcd" + "0".repeat(56) },
      verification: { trust_status: "OK", integrity_warnings: [] },
    },
    providerSetup: {
      data: {
        schema_version: "ui_provider_setup_console/v1",
        generated_at_utc: "2026-01-01T00:00:00Z",
        read_plane_only: true,
        mutation_authority: "x",
        execution_authority: "y",
        no_network_calls: true,
        no_secret_values: true,
        freshness_max_age_seconds: 3600,
        summary: {
          provider_count: 1,
          ready_count: 1,
          blocked_count: 0,
          action_required_count: 0,
          stale_count: 0,
          not_checked_count: 0,
          missing_secret_count: 0,
          public_no_signup_count: 0,
          keyed_provider_count: 0,
          pit_strong_count: 0,
        },
        entries: [],
      },
      isError: false,
      isLoading: false,
    },
    evidenceChain: {
      data: {
        schema_version: "ui_evidence_chain/v1",
        generated_at_utc: "2026-01-01T00:00:00Z",
        read_plane_only: true,
        mutation_authority: "x",
        promotion_authority: "y",
        execution_authority: "z",
        readonly: true,
        ok: true,
        degraded: [],
        summary: {
          event_count_total: 0,
          chain_issue_count_total: 0,
          decision_ledger_event_count: 0,
          decision_ledger_stream_count: 0,
          operator_action_event_count: 0,
          decision_ledger_chain_ok: true,
          operator_action_chain_ok: true,
        },
        streams: {},
        timeline: { entry_count: 0, returned_count: 0, limit: 250, entries: [] },
      },
      isError: false,
      isLoading: false,
    },
    ...overrides,
  };
}

describe("buildFirstRunDeploymentChecklist", () => {
  it("returns 12 ordered steps", () => {
    const steps = buildFirstRunDeploymentChecklist(baseInput());
    expect(steps).toHaveLength(12);
    expect(steps.map((s) => s.id)).toEqual([
      "backend_reachable",
      "health_probe",
      "readiness_probe",
      "production_auth",
      "ledger_configured",
      "migration_current",
      "backup_restore",
      "api_smoke",
      "provider_setup",
      "frontend_readiness",
      "deployment_evidence",
      "operator_signoff",
    ]);
  });

  it("uses UNKNOWN/PENDING when deployment read-plane is missing", () => {
    const steps = buildFirstRunDeploymentChecklist(
      baseInput({
        deployment: { data: null, isLoading: false, isError: true },
        readyz: { httpStatus: 503, body: null, isError: true, isLoading: false },
      }),
    );
    const ledger = steps.find((s) => s.id === "ledger_configured");
    expect(ledger?.status).toBe("UNKNOWN");
    const mig = steps.find((s) => s.id === "migration_current");
    expect(mig?.status).toBe("UNKNOWN");
  });

  it("surfaces FAIL when deployment checks fail", () => {
    const steps = buildFirstRunDeploymentChecklist(
      baseInput({
        deployment: {
          data: {
            checks: {
              environment_overrides_valid: false,
              private_key_material_absent: true,
              ledger_database_path_configured: true,
              ledger_path_resolved: true,
              schema_compatibility: true,
              ledger_backup_dir_configured: true,
              backup_root_writable: true,
            },
          },
          isLoading: false,
          isError: false,
        },
      }),
    );
    expect(steps.find((s) => s.id === "ledger_configured")?.status).toBe("FAIL");
  });

  it("does not mark deployment approved in checklist output", () => {
    const blob = JSON.stringify(buildFirstRunDeploymentChecklist(baseInput()));
    expect(blob.toUpperCase()).not.toContain("DEPLOYMENT_APPROVED");
  });
});

describe("FIRST_RUN_CLI_HINTS", () => {
  it("lists expected operator-only commands (never executed by UI)", () => {
    expect(FIRST_RUN_CLI_HINTS.length).toBeGreaterThanOrEqual(5);
    const joined = FIRST_RUN_CLI_HINTS.map((h) => h.command).join(" ");
    expect(joined).toContain("strategy-validator-deployment-env-check");
    expect(joined).toContain("--require-valid");
    expect(joined).toContain("strategy-validator-migrate --json");
    expect(joined).toContain("strategy-validator-single-tenant-preflight");
    expect(joined).toContain("--require-ready");
    expect(joined).toContain("strategy-validator-single-tenant-api-smoke");
    expect(joined).toContain("--require-pass");
    expect(joined).toContain("strategy-validator-single-tenant-evidence");
    expect(joined).not.toMatch(/sk-[a-zA-Z0-9]{10,}/);
  });
});

describe("suggestNextFirstRunCommand", () => {
  it("points to env check when ledger step fails first", () => {
    const steps = buildFirstRunDeploymentChecklist(
      baseInput({
        deployment: {
          data: {
            checks: {
              environment_overrides_valid: false,
              private_key_material_absent: true,
              ledger_database_path_configured: true,
              ledger_path_resolved: true,
              schema_compatibility: true,
              ledger_backup_dir_configured: true,
              backup_root_writable: true,
            },
          },
          isLoading: false,
          isError: false,
        },
      }),
    );
    const next = suggestNextFirstRunCommand(steps);
    expect(next?.stepId).toBe("ledger_configured");
    expect(next?.command).toContain("deployment-env-check");
  });
});

describe("firstRunTrustSummary", () => {
  it("extracts digest prefix without exposing secrets", () => {
    const t = firstRunTrustSummary({
      search_root: "/r",
      registry: { projection_digest_sha256: "abcdef0123456789" },
      verification: { trust_status: "RESTRICTED", integrity_warnings: ["a"] },
    });
    expect(t.digestPrefix).toBe("abcdef0123456789");
    expect(t.trustStatus).toBe("RESTRICTED");
    expect(t.warnings).toEqual(["a"]);
  });
});
