/** @vitest-environment node */

import { describe, expect, it } from "vitest";
import {
  buildOperatorHealthAlerts,
  severityRank,
  type OperatorHealthAlertsInput,
} from "./operator-health-alerts-model";

function baseInput(overrides: Partial<OperatorHealthAlertsInput> = {}): OperatorHealthAlertsInput {
  const d: OperatorHealthAlertsInput = {
    healthz: { data: { ok: true }, isError: false, isLoading: false },
    livez: { httpStatus: 200, isError: false, isLoading: false },
    readyz: {
      httpStatus: 200,
      body: { status: "READY", blockers: [], warnings: [], checked_at_utc: "2026-05-04T12:00:00Z" },
      isError: false,
      isLoading: false,
    },
    runtimeBody: {
      generated_at_utc: "2026-05-04T12:00:00Z",
      mutation_safety: {
        runtime_mode: "DEVELOPMENT",
        authorization_mode: "NON_PRODUCTION_BYPASS",
        token_configured: false,
        mutation_routes_safe: true,
        detail_code: "OK",
      },
    },
    runtimeError: false,
    runtimeLoading: false,
    mutationSafety: {
      runtime_mode: "DEVELOPMENT",
      authorization_mode: "NON_PRODUCTION_BYPASS",
      token_configured: false,
      mutation_routes_safe: true,
      detail_code: "OK",
    },
    evidencePayload: { generated_at_utc: "2026-05-04T12:00:00Z", registry: {} },
    evidenceError: false,
    evidenceLoading: false,
    cockpit: null,
    evidenceChain: {
      data: {
        schema_version: "x",
        generated_at_utc: "2026-05-04T12:00:00Z",
        read_plane_only: true,
        mutation_authority: "none",
        promotion_authority: "none",
        execution_authority: "none",
        readonly: true,
        ok: true,
        degraded: [],
        summary: {
          event_count_total: 1,
          chain_issue_count_total: 0,
          decision_ledger_event_count: 1,
          decision_ledger_stream_count: 1,
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
    providerSetup: {
      data: {
        schema_version: "ui_provider_setup_console/v1",
        generated_at_utc: "2026-05-04T12:00:00Z",
        read_plane_only: true,
        mutation_authority: "none",
        execution_authority: "none",
        no_network_calls: true,
        no_secret_values: true,
        freshness_max_age_seconds: 86400,
        summary: {
          provider_count: 0,
          ready_count: 0,
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
    providerHealth: { entries: [] },
    providerHealthError: false,
    deploymentReadiness: { checks: {}, blocker_codes: [], warning_codes: [], generated_at_utc: "2026-05-04T12:00:00Z" },
    deploymentReadinessError: false,
    deploymentReadinessLoading: false,
    facade: {
      schema_version: "ui_facade/v1",
      frontend_readiness_claimed: true,
      read_plane_only: true,
    },
    facadeError: false,
    facadeLoading: false,
    releaseReadiness: { status: "PRESENT", degraded: [], generated_at_utc: "2026-05-04T12:00:00Z" },
    releaseReadinessError: false,
    releaseReadinessLoading: false,
    researchOsDrift: { degraded: [], generated_at_utc: "2026-05-04T12:00:00Z" },
    researchOsDriftError: false,
    researchOsDriftLoading: false,
    paperExecution: null,
    paperExecutionError: false,
    paperBroker: null,
    paperBrokerError: false,
  };
  return { ...d, ...overrides };
}

describe("buildOperatorHealthAlerts", () => {
  it("emits UNKNOWN reachability when livez fails without crashing", () => {
    const r = buildOperatorHealthAlerts(
      baseInput({
        livez: { httpStatus: 503, isError: true, isLoading: false },
      }),
    );
    const live = r.alerts.find((a) => a.alert_id === "reachability:livez:fail");
    expect(live?.severity).toBe("CRITICAL");
  });

  it("maps readiness blockers to CRITICAL", () => {
    const r = buildOperatorHealthAlerts(
      baseInput({
        readyz: {
          httpStatus: 200,
          body: {
            status: "READY",
            blockers: ["LEDGER_UNREACHABLE"],
            warnings: [],
            checked_at_utc: "2026-05-04T12:00:00Z",
          },
          isError: false,
          isLoading: false,
        },
      }),
    );
    const blk = r.alerts.find((a) => a.alert_id === "readiness:blocker:0");
    expect(blk?.severity).toBe("CRITICAL");
    expect(blk?.summary).toContain("LEDGER");
  });

  it("flags production auth unsafe when mutation_routes_safe is false", () => {
    const r = buildOperatorHealthAlerts(
      baseInput({
        mutationSafety: {
          runtime_mode: "PRODUCTION",
          authorization_mode: "TOKEN_PROTECTED",
          token_configured: true,
          mutation_routes_safe: false,
          detail_code: "UNSAFE_ROUTES",
        },
        runtimeBody: {
          generated_at_utc: "2026-05-04T12:00:00Z",
          mutation_safety: {
            runtime_mode: "PRODUCTION",
            authorization_mode: "TOKEN_PROTECTED",
            token_configured: true,
            mutation_routes_safe: false,
            detail_code: "UNSAFE_ROUTES",
          },
        },
      }),
    );
    const a = r.alerts.find((x) => x.alert_id === "auth:mutation_unsafe");
    expect(a?.severity).toBe("CRITICAL");
    expect(a?.remediation.toLowerCase()).not.toMatch(/execute\s*live|live\s*order/i);
  });

  it("flags stale provider setup as WARNING", () => {
    const ps = baseInput().providerSetup.data!;
    const r = buildOperatorHealthAlerts(
      baseInput({
        providerSetup: {
          data: {
            ...ps,
            summary: { ...ps.summary, stale_count: 2 },
          },
          isError: false,
          isLoading: false,
        },
      }),
    );
    const a = r.alerts.find((x) => x.alert_id === "provider:stale");
    expect(a?.severity).toBe("WARNING");
  });

  it("flags broken evidence chain as CRITICAL", () => {
    const chain = baseInput().evidenceChain.data!;
    const r = buildOperatorHealthAlerts(
      baseInput({
        evidenceChain: {
          data: { ...chain, ok: false, summary: { ...chain.summary, decision_ledger_chain_ok: false } },
          isError: false,
          isLoading: false,
        },
      }),
    );
    const a = r.alerts.find((x) => x.alert_id === "ledger:chain:broken");
    expect(a?.severity).toBe("CRITICAL");
  });

  it("flags unclaimed frontend readiness as WARNING", () => {
    const r = buildOperatorHealthAlerts(
      baseInput({
        facade: { schema_version: "x", frontend_readiness_claimed: false, read_plane_only: true },
      }),
    );
    const a = r.alerts.find((x) => x.alert_id === "frontend:readiness:unclaimed");
    expect(a?.severity).toBe("WARNING");
    expect(a?.summary.toLowerCase()).not.toContain("approved");
  });

  it("sorts alerts with CRITICAL before WARNING before INFO before UNKNOWN", () => {
    const b = baseInput();
    const ps = b.providerSetup.data!;
    const r = buildOperatorHealthAlerts({
      ...b,
      livez: { httpStatus: 503, isError: true, isLoading: false },
      providerSetup: {
        data: { ...ps, summary: { ...ps.summary, stale_count: 1 } },
        isError: false,
        isLoading: false,
      },
    });
    for (let i = 1; i < r.alerts.length; i++) {
      expect(severityRank(r.alerts[i - 1]!.severity)).toBeLessThanOrEqual(severityRank(r.alerts[i]!.severity));
    }
  });

  it("does not embed obvious secret material in remediation for auth alerts", () => {
    const r = buildOperatorHealthAlerts(
      baseInput({
        mutationSafety: {
          runtime_mode: "PRODUCTION",
          authorization_mode: "TOKEN_PROTECTED",
          token_configured: false,
          mutation_routes_safe: true,
          detail_code: "OK",
        },
        runtimeBody: {
          generated_at_utc: "2026-05-04T12:00:00Z",
          mutation_safety: {
            runtime_mode: "PRODUCTION",
            authorization_mode: "TOKEN_PROTECTED",
            token_configured: false,
            mutation_routes_safe: true,
            detail_code: "OK",
          },
        },
      }),
    );
    const a = r.alerts.find((x) => x.alert_id === "auth:prod:token_missing");
    expect(a).toBeTruthy();
    expect(a!.remediation).not.toMatch(/sk-[a-z0-9]{10,}/i);
  });
});

describe("severityRank", () => {
  it("orders severities for sort", () => {
    expect(severityRank("CRITICAL")).toBeLessThan(severityRank("WARNING"));
    expect(severityRank("WARNING")).toBeLessThan(severityRank("INFO"));
    expect(severityRank("INFO")).toBeLessThan(severityRank("UNKNOWN"));
  });
});
