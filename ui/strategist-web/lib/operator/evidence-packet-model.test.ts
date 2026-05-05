import { describe, expect, it } from "vitest";
import { buildEvidencePacketModel, buildEvidenceRunbookMarkdown } from "./evidence-packet-model";
import type { UiEvidenceCockpitFields } from "./ui-evidence-cockpit";

const emptyCockpit: UiEvidenceCockpitFields = {
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
};

describe("buildEvidencePacketModel", () => {
  it("returns UNKNOWN posture when no read-plane payloads", () => {
    const m = buildEvidencePacketModel({
      evidence: null,
      evidenceChain: null,
      operatorActions: null,
      releaseReadiness: null,
      handoff: null,
      handoffSignoff: null,
      reviewJournal: null,
      exportLatest: null,
      cockpit: null,
    });
    expect(m.packet_status).toBe("UNKNOWN");
    expect(m.recommended_next_review_action).toBe("UNKNOWN");
    expect(m.rows.length).toBeGreaterThan(0);
    expect(m.rows[0]?.presence).toBe("UNKNOWN");
  });

  it("marks deployment manifest row PRESENT when cockpit shows PASS + path", () => {
    const cockpit: UiEvidenceCockpitFields = {
      ...emptyCockpit,
      deployment_status: "PASS",
      deployment_evidence_ok: true,
      deployment_evidence_manifest_path: "scratch/x/deployment-evidence.json",
    };
    const m = buildEvidencePacketModel({
      evidence: { schema_version: "ui_evidence_dashboard/v1", generated_at_utc: "2026-01-01T00:00:00Z", registry: {} },
      evidenceChain: { summary: { operator_action_chain_ok: true }, degraded: [] },
      operatorActions: { event_count: 1, chain_ok: true },
      releaseReadiness: {},
      handoff: {},
      handoffSignoff: {},
      reviewJournal: {},
      exportLatest: {},
      cockpit,
    });
    const row = m.rows.find((r) => r.__id === "pkt-deployment-evidence-manifest");
    expect(row?.presence).toBe("PRESENT");
  });

  it("includes registry_table artifact rows with digest prefix when present on disk", () => {
    const m = buildEvidencePacketModel({
      evidence: {
        schema_version: "ui_evidence_dashboard/v1",
        generated_at_utc: "2026-01-01T00:00:00Z",
        registry: { projection_digest_sha256: "abcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcd" },
        registry_table: [
          {
            artifact_label: "DAILY_CHECKLIST.json",
            path: "docs/artifacts/DAILY_CHECKLIST.json",
            exists: true,
            sha256: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
          },
        ],
      },
      evidenceChain: { summary: { operator_action_chain_ok: true }, degraded: [] },
      operatorActions: { event_count: 0, chain_ok: true },
      releaseReadiness: {},
      handoff: {},
      handoffSignoff: {},
      reviewJournal: {},
      exportLatest: {},
      cockpit: emptyCockpit,
    });
    const art = m.rows.find((r) => r.__id === "pkt-registry-artifact-0");
    expect(art?.presence).toBe("PRESENT");
    expect(art?.digest_prefix).toContain("0123456789ab");
  });
});

describe("buildEvidenceRunbookMarkdown", () => {
  it("does not embed obvious secret markers", () => {
    const m = buildEvidencePacketModel({
      evidence: { schema_version: "ui_evidence_dashboard/v1", generated_at_utc: "2026-01-01T00:00:00Z", registry: {} },
      evidenceChain: {},
      operatorActions: {},
      releaseReadiness: {},
      handoff: {},
      handoffSignoff: {},
      reviewJournal: {},
      exportLatest: {},
      cockpit: emptyCockpit,
    });
    const md = buildEvidenceRunbookMarkdown(m);
    expect(md.toLowerCase()).not.toContain("sk-live");
    expect(md.toLowerCase()).not.toContain("bearer ");
    expect(md).toContain("Not deployment approval");
  });
});
