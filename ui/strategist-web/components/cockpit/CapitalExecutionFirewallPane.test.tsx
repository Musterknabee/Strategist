/** @vitest-environment jsdom */

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CapitalExecutionFirewallPane } from "./CapitalExecutionFirewallPane";

afterEach(() => cleanup());

describe("CapitalExecutionFirewallPane", () => {
  it("renders degraded UNKNOWN posture without crashing when sources are empty", () => {
    const openInspector = vi.fn();
    render(
      <CapitalExecutionFirewallPane
        paperExecution={null}
        paperBroker={null}
        paperTracking={null}
        providerSetup={null}
        providerHealth={null}
        runtimeMutationSafety={null}
        executionAuthorityHint={null}
        queryFailed
        openInspector={openInspector}
      />,
    );
    expect(screen.getByTestId("cockpit-execution-firewall")).toBeTruthy();
    expect(screen.getByTestId("cockpit-firewall-safety-label-UNKNOWN")).toBeTruthy();
  });

  it("renders paper-only and live-blocked labels when model derives them", () => {
    render(
      <CapitalExecutionFirewallPane
        paperExecution={{
          no_live_trading: true,
          no_browser_orders: true,
          no_network_calls: true,
          execution_authority: "LIVE_BLOCKED",
          mutation_authority: "NONE",
          paper_submission_authority: "CLI_ONLY",
          summary: {
            broker_policy_status: "PAPER_READY",
            submission_receipt_count: 0,
            dry_run_artifact_count: 1,
            evidence_freshness_status: "CURRENT",
            position_reconciliation_status: "RECONCILED",
          },
          dry_run_results: [{ artifact_sha256: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" }],
        }}
        paperBroker={{ policy_status: "PAPER_READY", blockers: [] }}
        paperTracking={{}}
        providerSetup={{ summary: { blocked_count: 0 } }}
        providerHealth={{}}
        runtimeMutationSafety={null}
        executionAuthorityHint={null}
        queryFailed={false}
        openInspector={vi.fn()}
      />,
    );
    expect(screen.getByTestId("cockpit-firewall-safety-label-PAPER_ONLY")).toBeTruthy();
    expect(screen.getByTestId("cockpit-firewall-safety-label-LIVE_BLOCKED")).toBeTruthy();
    expect(screen.getByTestId("cockpit-firewall-safety-label-NO_NETWORK_CALLS")).toBeTruthy();
  });

  it("opens inspector with digest copy from full hash, not truncated prefix", () => {
    const openInspector = vi.fn();
    const sha = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
    render(
      <CapitalExecutionFirewallPane
        paperExecution={{
          summary: { latest_evidence_bundle_sha256: sha, submission_receipt_count: 0, dry_run_artifact_count: 0 },
        }}
        paperBroker={null}
        paperTracking={null}
        providerSetup={null}
        providerHealth={null}
        runtimeMutationSafety={null}
        executionAuthorityHint={null}
        queryFailed={false}
        openInspector={openInspector}
      />,
    );
    fireEvent.click(screen.getByTitle("Inspect"));
    expect(openInspector).toHaveBeenCalled();
    const arg = openInspector.mock.calls[0][0] as { digestToCopy?: string };
    expect(arg.digestToCopy).toBe(sha);
  });

  it("does not render raw secret-looking strings in the pane tree", () => {
    const { container } = render(
      <CapitalExecutionFirewallPane
        paperExecution={{
          summary: { broker_policy_status: "PAPER_READY" },
          submission_receipts: [{ broker_order_id: "x", artifact_path: "/var/secrets.env" }],
        }}
        paperBroker={null}
        paperTracking={null}
        providerSetup={null}
        providerHealth={null}
        runtimeMutationSafety={null}
        executionAuthorityHint={null}
        queryFailed={false}
        openInspector={vi.fn()}
      />,
    );
    expect(container.textContent).not.toMatch(/ALPACA_API_SECRET/i);
  });
});
