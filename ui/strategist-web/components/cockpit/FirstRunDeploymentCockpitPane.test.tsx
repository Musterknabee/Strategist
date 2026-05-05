/** @vitest-environment jsdom */

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { FirstRunDeploymentCockpitPane } from "./FirstRunDeploymentCockpitPane";
import type { FirstRunChecklistInput } from "@/lib/operator/first-run-deployment-checklist";

const openInspector = vi.fn();

const minimalInput: FirstRunChecklistInput = {
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
  readyz: {
    httpStatus: 200,
    body: { status: "READY", checks: { schema_current: true }, blockers: [], warnings: [] },
    isError: false,
    isLoading: false,
  },
  healthz: { isError: false, isLoading: false, data: { ok: true } },
  livez: { httpStatus: 200, isError: false, isLoading: false },
  facade: {
    data: {
      schema_version: "x",
      surface: "ui",
      frontend_expected_package: "ui/strategist-web",
      frontend_package_present: false,
      frontend_readiness_claimed: false,
      read_plane_only: true,
      mutation_route: "/ui/commands/{action}",
      routes: [],
      frontend_operator_console_hint: "Opt-in claim is not automatic certification.",
    },
    isError: false,
  },
  mutationSafety: {
    runtime_mode: "DEV",
    authorization_mode: "NON_PRODUCTION_BYPASS",
    token_configured: false,
    mutation_routes_safe: true,
    detail_code: "X",
  },
  cockpit: {
    deployment_status: "UNKNOWN",
    deployment_evidence_ok: null,
    operator_decision: "UNKNOWN",
    manual_operator_signoff_present: null,
    api_smoke_status: "UNKNOWN",
    api_smoke_ok: null,
    backup_restore_ok: null,
    ledger_integrity_ok: null,
    ci_local_verify_ok: null,
    frontend_readiness_status: "UNKNOWN",
    evidence_generated_at_utc: undefined,
  },
  evidencePayload: { verification: { trust_status: "UNKNOWN", integrity_warnings: [] }, registry: {} },
  providerSetup: {
    data: {
      schema_version: "ui_provider_setup_console/v1",
      generated_at_utc: "2026-01-01T00:00:00Z",
      read_plane_only: true,
      mutation_authority: "m",
      execution_authority: "e",
      no_network_calls: true,
      no_secret_values: true,
      freshness_max_age_seconds: 1,
      summary: {
        provider_count: 1,
        ready_count: 0,
        blocked_count: 1,
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
    data: null,
    isError: false,
    isLoading: false,
  },
};

afterEach(() => {
  cleanup();
});

describe("FirstRunDeploymentCockpitPane / SingleTenantFirstRunWizard", () => {
  it("renders all first-run checklist steps", () => {
    render(
      <FirstRunDeploymentCockpitPane
        checklistInput={minimalInput}
        deploymentBlockerCodes={["BACKUP_ROOT_NOT_WRITABLE"]}
        deploymentWarningCodes={["LEDGE_HASH"]}
        facadeOperatorHint="Hint from facade."
        openInspector={openInspector}
      />,
    );
    expect(screen.getByTestId("cockpit-first-run-deployment")).toBeTruthy();
    for (const id of [
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
    ]) {
      expect(screen.getByTestId(`first-run-step-${id}`)).toBeTruthy();
    }
  });

  it("renders CLI copy buttons without executing commands", () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText } });
    render(
      <FirstRunDeploymentCockpitPane
        checklistInput={minimalInput}
        deploymentBlockerCodes={[]}
        deploymentWarningCodes={[]}
        facadeOperatorHint={null}
        openInspector={openInspector}
      />,
    );
    const root = screen.getByTestId("cockpit-first-run-cli-hints");
    const copies = root.querySelectorAll('[data-testid^="cockpit-first-run-cli-hints-copy-"]');
    expect(copies.length).toBeGreaterThan(0);
    fireEvent.click(copies[0] as HTMLElement);
    expect(writeText).toHaveBeenCalledTimes(1);
    expect(writeText.mock.calls[0][0]).toContain("strategy-validator");
    vi.unstubAllGlobals();
  });

  it("shows frontend readiness explanation", () => {
    render(
      <FirstRunDeploymentCockpitPane
        checklistInput={minimalInput}
        deploymentBlockerCodes={[]}
        deploymentWarningCodes={[]}
        facadeOperatorHint="Custom opt-in explanation."
        openInspector={openInspector}
      />,
    );
    expect(screen.getByTestId("first-run-frontend-readiness-copy").textContent).toContain("Package-present");
    expect(screen.getByText(/Custom opt-in explanation/)).toBeTruthy();
  });

  it("shows provider summary counts without secret values", () => {
    const { container } = render(
      <FirstRunDeploymentCockpitPane
        checklistInput={minimalInput}
        deploymentBlockerCodes={[]}
        deploymentWarningCodes={[]}
        facadeOperatorHint={null}
        openInspector={openInspector}
      />,
    );
    expect(screen.getByTestId("first-run-provider-summary")).toBeTruthy();
    expect(container.textContent).not.toContain("sk-live-fake-secret");
  });

  it("shows suggested next when a step is not fully pass", () => {
    render(
      <FirstRunDeploymentCockpitPane
        checklistInput={minimalInput}
        deploymentBlockerCodes={[]}
        deploymentWarningCodes={[]}
        facadeOperatorHint={null}
        openInspector={openInspector}
      />,
    );
    expect(screen.getByTestId("first-run-suggested-next")).toBeTruthy();
  });
});
