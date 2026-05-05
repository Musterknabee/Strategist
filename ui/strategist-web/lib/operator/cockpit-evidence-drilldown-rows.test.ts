import { describe, expect, it } from "vitest";
import { buildPaperExecutionEvidenceRows, buildResearchOsEvidenceRows, researchOsAggregateDigest } from "./cockpit-evidence-drilldown-rows";

describe("buildResearchOsEvidenceRows", () => {
  it("fills UNKNOWN/PENDING when status aggregate is missing", () => {
    const rows = buildResearchOsEvidenceRows(null);
    expect(rows.length).toBeGreaterThan(0);
    expect(rows.every((r) => r.status === "UNKNOWN")).toBe(true);
    expect(rows.every((r) => r.at === "PENDING")).toBe(true);
  });

  it("surfaces closure, drift, and policy gate signals from nested payloads", () => {
    const status = {
      schema_version: "ui_research_os_status/v1",
      generated_at_utc: "2026-05-01T12:00:00Z",
      read_plane_only: true,
      research_os_closure_latest: {
        status: "PRESENT",
        generated_at_utc: "2026-05-01T12:00:00Z",
        latest: {
          status: "COMPLETE",
          trust_banner: "TRUSTED",
          manifest_sha256: "abcdef0123456789abcdef0123456789",
          blockers: [],
          warnings: [],
        },
        degraded: [],
      },
      research_os_attestation_latest: {
        status: "PRESENT",
        generated_at_utc: "2026-05-01T12:00:00Z",
        latest_verification: { status: "VERIFIED", trust_banner: "TRUSTED", blockers: [], warnings: [] },
        latest_attestation: { decision: "ACKNOWLEDGED", blockers: [], warnings: [] },
        degraded: [],
      },
      research_os_evidence_drift_latest: {
        status: "PRESENT",
        generated_at_utc: "2026-05-01T12:00:00Z",
        latest: { status: "READY", trust_banner: "TRUSTED", artifact_sha256: "fedcba0123456789fedcba0123456789", blockers: [], warnings: [] },
        degraded: [],
      },
      research_os_policy_gate_latest: {
        status: "PRESENT",
        latest: { decision: "PASS", trust_banner: "TRUSTED" },
        degraded: [],
      },
      research_os_release_readiness_latest: { status: "NOT_PRESENT", degraded: ["NO_REPORT"] },
      research_os_exception_latest: { status: "NOT_PRESENT", degraded: [] },
      research_os_remediation_latest: { status: "NOT_PRESENT", degraded: [] },
    };
    const rows = buildResearchOsEvidenceRows(status);
    const closure = rows.find((r) => r.__id === "ros:closure");
    const drift = rows.find((r) => r.__id === "ros:drift");
    const gate = rows.find((r) => r.__id === "ros:policy_gate");
    expect(closure?.status).toBe("COMPLETE");
    expect(closure?.digestFull).toContain("abcdef");
    expect(drift?.status).toBe("READY");
    expect(gate?.status).toBe("PASS");
  });

  it("researchOsAggregateDigest prefers runtime demo manifest sha256", () => {
    const d = researchOsAggregateDigest({
      runtime_demo_manifest: { manifest_sha256: "11111111111111111111111111111111" },
      research_os_closure_latest: { latest: { manifest_sha256: "22222222222222222222222222222222" } },
    });
    expect(d).toBe("11111111111111111111111111111111");
  });
});

describe("buildPaperExecutionEvidenceRows", () => {
  it("includes PAPER_ONLY and LIVE_BLOCKED hints when authorities and flags indicate", () => {
    const rows = buildPaperExecutionEvidenceRows({
      schema_version: "paper_execution_cockpit/v1",
      generated_at_utc: "2026-05-01T12:00:00Z",
      read_plane_only: true,
      no_live_trading: true,
      no_browser_orders: true,
      execution_authority: "LIVE_BLOCKED",
      promotion_authority: "PAPER_ONLY_GATE",
      summary: {
        broker_policy_status: "PAPER_READY",
        paper_submission_capability: "CLI_ONLY",
        submission_guard_blocker_count: 2,
        evidence_bundle_blocker_count: 1,
        timeline_blocker_count: 0,
        evidence_freshness_blocker_count: 1,
        timeline_warning_count: 3,
        position_reconciliation_warning_count: 1,
        latest_evidence_bundle_sha256: "0123456789abcdef0123456789abcdef",
        latest_evidence_bundle_trust_banner: "TRUST_RESTRICTED",
        latest_evidence_bundle_status: "SEALED",
        selected_intent_dry_run_status: "OK",
      },
      dry_run_results: [{ status: "OK", trust_banner: "TRUSTED", artifact_sha256: "a".repeat(64), generated_at_utc: "2026-05-01T11:00:00Z" }],
    });
    const posture = rows.find((r) => r.__id === "paper:posture");
    expect(posture?.status).toContain("PAPER_ONLY");
    expect(posture?.status).toContain("LIVE_BLOCKED");
    expect(posture?.blockers).toBe(4);
    expect(posture?.warnings).toBe(4);
    expect(posture?.digestPreview.length).toBeGreaterThan(4);
  });
});
