/** @vitest-environment jsdom */

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { OperatorHealthAlertsPane } from "./OperatorHealthAlertsPane";
import type { OperatorHealthAlertsInput } from "@/lib/operator/operator-health-alerts-model";

afterEach(() => cleanup());

function minimalInput(overrides: Partial<OperatorHealthAlertsInput> = {}): OperatorHealthAlertsInput {
  const i: OperatorHealthAlertsInput = {
    healthz: { data: null, isError: false, isLoading: true },
    livez: { httpStatus: undefined, isError: false, isLoading: true },
    readyz: { httpStatus: undefined, body: null, isError: false, isLoading: true },
    runtimeBody: null,
    runtimeError: false,
    runtimeLoading: true,
    mutationSafety: null,
    evidencePayload: null,
    evidenceError: false,
    evidenceLoading: true,
    cockpit: null,
    evidenceChain: { data: null, isError: false, isLoading: true },
    providerSetup: { data: null, isError: false, isLoading: true },
    providerHealth: null,
    providerHealthError: false,
    deploymentReadiness: null,
    deploymentReadinessError: false,
    deploymentReadinessLoading: true,
    facade: null,
    facadeError: false,
    facadeLoading: true,
    releaseReadiness: null,
    releaseReadinessError: false,
    releaseReadinessLoading: true,
    researchOsDrift: null,
    researchOsDriftError: false,
    researchOsDriftLoading: true,
    paperExecution: null,
    paperExecutionError: false,
    paperBroker: null,
    paperBrokerError: false,
  };
  return { ...i, ...overrides };
}

describe("OperatorHealthAlertsPane", () => {
  it("renders with pending/unknown posture when probes are loading", () => {
    const openInspector = vi.fn();
    render(<OperatorHealthAlertsPane healthInput={minimalInput()} queryFailed={false} openInspector={openInspector} />);
    expect(screen.getByTestId("cockpit-operator-health-alerts")).toBeTruthy();
    expect(screen.getByTestId("cockpit-health-alert-counts")).toBeTruthy();
  });

  it("opens inspector when an alert row is clicked", () => {
    const openInspector = vi.fn();
    const input = minimalInput({
      healthz: { data: { ok: true }, isError: false, isLoading: false },
      livez: { httpStatus: 200, isError: false, isLoading: false },
      readyz: {
        httpStatus: 200,
        body: { status: "READY", blockers: [], warnings: [], checked_at_utc: "2026-05-04T12:00:00Z" },
        isError: false,
        isLoading: false,
      },
      runtimeLoading: false,
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
      mutationSafety: {
        runtime_mode: "DEVELOPMENT",
        authorization_mode: "NON_PRODUCTION_BYPASS",
        token_configured: false,
        mutation_routes_safe: true,
        detail_code: "OK",
      },
      evidenceLoading: false,
      evidencePayload: { generated_at_utc: "2026-05-04T12:00:00Z" },
      evidenceChain: {
        isLoading: false,
        isError: false,
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
      },
      providerSetup: { isLoading: false, isError: false, data: null },
      deploymentReadinessLoading: false,
      deploymentReadinessError: true,
      facadeLoading: false,
      facade: { frontend_readiness_claimed: false, schema_version: "x", read_plane_only: true },
      releaseReadinessLoading: false,
      releaseReadiness: { status: "MISSING", degraded: ["X"], generated_at_utc: "2026-05-04T12:00:00Z" },
      researchOsDriftLoading: false,
      researchOsDrift: { degraded: ["D"], generated_at_utc: "2026-05-04T12:00:00Z" },
    });
    render(<OperatorHealthAlertsPane healthInput={input} queryFailed={false} openInspector={openInspector} />);
    const btn = screen.getByTestId("cockpit-health-row-open-frontend:readiness:unclaimed");
    fireEvent.click(btn);
    expect(openInspector).toHaveBeenCalled();
  });

  it("filters table rows by severity", () => {
    const input = minimalInput({
      healthz: { data: { ok: true }, isError: false, isLoading: false },
      livez: { httpStatus: 200, isError: false, isLoading: false },
      readyz: {
        httpStatus: 200,
        body: {
          status: "READY",
          blockers: ["B1"],
          warnings: [],
          checked_at_utc: "2026-05-04T12:00:00Z",
        },
        isError: false,
        isLoading: false,
      },
      runtimeLoading: false,
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
      mutationSafety: {
        runtime_mode: "DEVELOPMENT",
        authorization_mode: "NON_PRODUCTION_BYPASS",
        token_configured: false,
        mutation_routes_safe: true,
        detail_code: "OK",
      },
      evidenceLoading: false,
      evidencePayload: { generated_at_utc: "2026-05-04T12:00:00Z" },
      evidenceChain: { isLoading: false, isError: false, data: null },
      providerSetup: { isLoading: false, isError: false, data: null },
      deploymentReadinessLoading: false,
      deploymentReadinessError: true,
      facadeLoading: false,
      facade: { frontend_readiness_claimed: true, schema_version: "x", read_plane_only: true },
      releaseReadinessLoading: false,
      releaseReadiness: { status: "PRESENT", degraded: [] },
      researchOsDriftLoading: false,
      researchOsDrift: { degraded: [] },
    });
    render(<OperatorHealthAlertsPane healthInput={input} queryFailed={false} openInspector={vi.fn()} />);
    fireEvent.change(screen.getByLabelText("Filter alerts by severity"), { target: { value: "CRITICAL" } });
    expect(screen.getByTestId("cockpit-health-row-sev-readiness:blocker:0")).toBeTruthy();
    expect(screen.queryByTestId("cockpit-health-row-open-frontend:readiness:unclaimed")).toBeNull();
  });
});
