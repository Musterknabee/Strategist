import { describe, expect, it } from "vitest";
import type { UiEvidenceCockpitFields } from "@/lib/operator/ui-evidence-cockpit";
import { RELEASE_CONTROL_COMMAND_HINTS, buildReleaseControlModel } from "./release-control-model";

const emptyChain = { degraded: [], summary: { chain_issue_count_total: 0 } };

function base(overrides: Partial<Parameters<typeof buildReleaseControlModel>[0]> = {}) {
  return {
    facade: { frontend_readiness_claimed: false, frontend_package_present: true },
    evidence: {
      deployment_status: "UNKNOWN",
      registry: {},
      verification: {},
    },
    evidenceChain: emptyChain,
    releaseReadiness: {
      schema_version: "ui_research_os_release_readiness/v1",
      degraded: ["NO_RESEARCH_OS_RELEASE_READINESS_REPORT"],
      latest: null,
    },
    handoff: { degraded: ["NO_RESEARCH_OS_HANDOFF_PACK"], latest: null },
    handoffSignoff: { latest_verification: null, latest_signoff: null, degraded: ["NO_RESEARCH_OS_HANDOFF_VERIFICATION_RESULT"] },
    reviewJournal: { status: "NOT_PRESENT", degraded: ["NO_RESEARCH_OS_REVIEW_JOURNAL"], latest: null },
    cockpit: null,
    ...overrides,
  };
}

describe("buildReleaseControlModel", () => {
  it("marks readiness UNKNOWN and surfaces GENERATE_RELEASE_CANDIDATE when bootstrap evidence is absent", () => {
    const m = buildReleaseControlModel(base({ cockpit: null }));
    expect(m.readiness_bucket).toBe("UNKNOWN");
    expect(m.next_action).toBe("GENERATE_RELEASE_CANDIDATE");
  });

  it("maps PASS release readiness and sets digest on readiness row", () => {
    const m = buildReleaseControlModel(
      base({
        facade: { frontend_readiness_claimed: true, frontend_package_present: true },
        releaseReadiness: {
          degraded: [],
          latest: {
            status: "READY_FOR_REVIEW",
            decision: "SINGLE_TENANT_REVIEW_READY",
            trust_banner: "TRUSTED",
            manifest_sha256: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            generated_at_utc: "2026-05-01T12:00:00Z",
            criteria: [{ criterion_id: "c1", status: "PASS", title: "t" }],
          },
        },
        evidence: {
          deployment_status: "PASS",
          deployment_evidence_manifest_path: "/tmp/deployment-evidence.json",
          deployment_evidence_ok: true,
          manual_operator_signoff_present: true,
          frontend_readiness_status: "CLAIMED",
          registry: { projection_digest_sha256: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" },
        },
        handoffSignoff: {
          degraded: [],
          latest_verification: { status: "VERIFIED", verified_at_utc: "2026-05-01T12:00:00Z" },
          latest_signoff: { decision: "ACKNOWLEDGED", signed_at_utc: "2026-05-01T12:01:00Z", trust_banner: "TRUSTED" },
        },
        cockpit: {
          deployment_status: "PASS",
          deployment_evidence_ok: true,
          deployment_evidence_manifest_path: "/tmp/deployment-evidence.json",
          manual_operator_signoff_present: true,
          frontend_readiness_status: "CLAIMED",
          ci_local_verify_ok: true,
          evidence_generated_at_utc: "2026-05-01T12:00:00Z",
          operator_decision: "APPROVED",
          api_smoke_status: "PASS",
          api_smoke_ok: true,
          backup_restore_ok: true,
          ledger_integrity_ok: true,
        } satisfies UiEvidenceCockpitFields,
      }),
    );
    expect(m.readiness_bucket).toBe("PASS");
    expect(m.next_action).toBe("READY_FOR_OPERATOR_DECISION");
    const rr = m.rows.find((r) => r.__id === "rc-release-readiness");
    expect(rr?.digest_full?.length).toBe(64);
  });

  it("maps FAIL readiness when a criterion fails", () => {
    const m = buildReleaseControlModel(
      base({
        releaseReadiness: {
          degraded: [],
          latest: {
            status: "BLOCKED",
            decision: "BLOCKED_BY_EVIDENCE",
            criteria: [{ criterion_id: "x", status: "FAIL", title: "t" }],
            manifest_sha256: "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          },
        },
      }),
    );
    expect(m.readiness_bucket).toBe("FAIL");
    expect(m.next_action).toBe("RESOLVE_RELEASE_BLOCKERS");
  });

  it("prefers VERIFY_CLEAN_ARCHIVE when ci_local_verify fails", () => {
    const m = buildReleaseControlModel(
      base({
        releaseReadiness: {
          degraded: [],
          latest: {
            status: "READY_FOR_REVIEW",
            decision: "SINGLE_TENANT_REVIEW_READY",
            criteria: [],
            manifest_sha256: "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
          },
        },
        evidence: {
          deployment_status: "PASS",
          deployment_evidence_manifest_path: "/e.json",
          deployment_evidence_ok: true,
        },
        cockpit: {
          deployment_status: "PASS",
          deployment_evidence_ok: true,
          deployment_evidence_manifest_path: "/e.json",
          ci_local_verify_ok: false,
          manual_operator_signoff_present: true,
          frontend_readiness_status: "CLAIMED",
          operator_decision: "APPROVED",
          api_smoke_status: "PASS",
          api_smoke_ok: true,
          backup_restore_ok: true,
          ledger_integrity_ok: true,
          evidence_generated_at_utc: "2026-05-01T12:00:00Z",
        } satisfies UiEvidenceCockpitFields,
        handoffSignoff: {
          degraded: [],
          latest_verification: { status: "VERIFIED" },
          latest_signoff: { decision: "ACKNOWLEDGED", signed_at_utc: "2026-05-01T12:00:00Z" },
        },
      }),
    );
    expect(m.next_action).toBe("VERIFY_CLEAN_ARCHIVE");
  });
});

describe("RELEASE_CONTROL_COMMAND_HINTS", () => {
  it("uses pyproject script names for strategist CLIs", () => {
    expect(RELEASE_CONTROL_COMMAND_HINTS.rcGenerate).toContain("strategy-validator-release-candidate generate");
    expect(RELEASE_CONTROL_COMMAND_HINTS.stEvidence).toContain("strategy-validator-single-tenant-evidence");
    expect(RELEASE_CONTROL_COMMAND_HINTS.researchOsReleaseReadiness).toContain(
      "strategy-validator-research-os-release-readiness",
    );
  });
});
