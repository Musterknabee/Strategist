/** @vitest-environment node */

import { describe, expect, it } from "vitest";
import { buildExecutionFirewallModel, reviewActionIsReadPlaneSafe, type ExecutionFirewallReviewAction } from "./execution-firewall-model";

const ALL_REVIEW_ACTIONS: ExecutionFirewallReviewAction[] = [
  "RUN_PAPER_EXECUTION_DRY_RUN",
  "REVIEW_PAPER_ONLY_BOUNDARY",
  "GENERATE_DRY_RUN_EVIDENCE",
  "VERIFY_SUBMISSION_MATCHES_SELECTION",
  "REVIEW_POSITION_RECONCILIATION",
  "REVIEW_BROKER_PROVIDER_SETUP",
  "REFRESH_EXECUTION_EVIDENCE",
  "UNKNOWN",
];

describe("buildExecutionFirewallModel", () => {
  it("returns UNKNOWN/PENDING-safe posture when paper execution is absent", () => {
    const m = buildExecutionFirewallModel({
      paperExecution: null,
      paperBroker: null,
      paperTracking: null,
      providerSetup: null,
      providerHealth: null,
      runtimeMutationSafety: null,
      executionAuthorityHint: null,
      queryFailed: false,
    });
    expect(m.safety_labels).toContain("UNKNOWN");
    expect(m.recommended_review_action).toBe("RUN_PAPER_EXECUTION_DRY_RUN");
    expect(m.capital_mode).toMatch(/PAPER_ONLY|UNKNOWN|LIVE_BLOCKED/);
    expect(m.digest_prefix).toBe("—");
    expect(m.digest_full).toBeNull();
  });

  it("surfaces paper-only and live-blocked when execution payload declares boundaries", () => {
    const m = buildExecutionFirewallModel({
      paperExecution: {
        schema_version: "ui_paper_execution_cockpit/v1",
        generated_at_utc: "2026-05-04T12:00:00Z",
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
        dry_run_results: [{ artifact_sha256: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", artifact_path: "/safe/out/dry.json" }],
      },
      paperBroker: { policy_status: "PAPER_READY", blockers: [], warnings: [] },
      paperTracking: {},
      providerSetup: { summary: { blocked_count: 0 } },
      providerHealth: {},
      runtimeMutationSafety: null,
      executionAuthorityHint: null,
      queryFailed: false,
    });
    expect(m.safety_labels).toContain("PAPER_ONLY");
    expect(m.safety_labels).toContain("LIVE_BLOCKED");
    expect(m.safety_labels).toContain("NO_NETWORK_CALLS");
    expect(m.safety_labels).toContain("DRY_RUN_ONLY");
    expect(m.reconciliation_status.toUpperCase()).toContain("RECONCILED");
    expect(m.safety_labels).toContain("POSITION_RECONCILED");
  });

  it("prefers broker/provider setup review when broker blockers or setup blocked", () => {
    const blocked = buildExecutionFirewallModel({
      paperExecution: {
        schema_version: "ui_paper_execution_cockpit/v1",
        generated_at_utc: "2026-05-04T12:00:00Z",
        no_live_trading: true,
        no_browser_orders: true,
        summary: {
          broker_policy_status: "BLOCKED",
          submission_receipt_count: 0,
          dry_run_artifact_count: 1,
          evidence_freshness_status: "CURRENT",
        },
        dry_run_results: [{}],
      },
      paperBroker: { policy_status: "BLOCKED", blockers: ["no paper endpoint"], warnings: [] },
      paperTracking: {},
      providerSetup: { summary: { blocked_count: 2 } },
      providerHealth: {},
      runtimeMutationSafety: null,
      executionAuthorityHint: null,
      queryFailed: false,
    });
    expect(blocked.recommended_review_action).toBe("REVIEW_BROKER_PROVIDER_SETUP");
  });

  it("exposes digest prefix from bundle hash when present", () => {
    const m = buildExecutionFirewallModel({
      paperExecution: {
        summary: {
          latest_evidence_bundle_sha256: "0123456789abcdef0123456789abcdef",
          submission_receipt_count: 0,
          dry_run_artifact_count: 0,
        },
      },
      paperBroker: null,
      paperTracking: null,
      providerSetup: null,
      providerHealth: null,
      runtimeMutationSafety: null,
      executionAuthorityHint: null,
      queryFailed: false,
    });
    expect(m.digest_prefix).toMatch(/^0123456789ab/);
    expect(m.digest_full).toBe("0123456789abcdef0123456789abcdef");
  });

  it("counts blockers and warnings from receipt and reconciliation", () => {
    const m = buildExecutionFirewallModel({
      paperExecution: {
        summary: {
          submission_receipt_count: 1,
          dry_run_artifact_count: 1,
          evidence_freshness_status: "CURRENT",
          position_reconciliation_status: "PENDING",
          position_reconciliation_blocker_count: 1,
        },
        submission_receipts: [
          {
            broker_order_id: "paper-ord-1",
            blockers: ["b1"],
            warnings: ["w1"],
            submission_intent_matches_selection: true,
            linked_dry_run_ok: true,
          },
        ],
        position_reconciliation: {
          status: "PENDING",
          blockers: ["qty_mismatch"],
          warnings: ["wr"],
          observed_position_qty: 0,
          filled_qty: 1,
        },
      },
      paperBroker: null,
      paperTracking: null,
      providerSetup: null,
      providerHealth: null,
      runtimeMutationSafety: null,
      executionAuthorityHint: null,
      queryFailed: false,
    });
    expect(m.blocker_count).toBeGreaterThan(0);
    expect(m.warning_count).toBeGreaterThan(0);
    expect(m.proof_lines.some((l) => l.includes("broker_order_id="))).toBe(true);
    expect(m.safety_labels).toContain("RECONCILIATION_PENDING");
  });
});

describe("reviewActionIsReadPlaneSafe", () => {
  it("treats all defined review actions as read-plane safe (no live execution copy)", () => {
    for (const a of ALL_REVIEW_ACTIONS) {
      expect(reviewActionIsReadPlaneSafe(a), a).toBe(true);
    }
  });
});
