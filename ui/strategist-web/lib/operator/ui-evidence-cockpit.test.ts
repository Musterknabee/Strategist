import { describe, expect, it } from "vitest";
import { formatCockpitOk, readUiEvidenceCockpit } from "./ui-evidence-cockpit";

describe("readUiEvidenceCockpit", () => {
  it("reads explicit backend cockpit keys", () => {
    const c = readUiEvidenceCockpit({
      deployment_status: "PASS",
      deployment_evidence_ok: true,
      api_smoke_status: "PASS",
      api_smoke_ok: true,
      backup_restore_ok: null,
      ledger_integrity_ok: false,
      ci_local_verify_ok: undefined,
      operator_decision: "KEEP_CURRENT_RELEASE",
      manual_operator_signoff_present: true,
      frontend_readiness_status: "NOT_CLAIMED",
      evidence_generated_at_utc: "2026-01-01T00:00:00Z",
    });
    expect(c?.deployment_status).toBe("PASS");
    expect(c?.api_smoke_ok).toBe(true);
    expect(c?.ledger_integrity_ok).toBe(false);
    expect(c?.backup_restore_ok).toBeNull();
  });
});

describe("formatCockpitOk", () => {
  it("formats tri-state for operator tables", () => {
    expect(formatCockpitOk(true)).toBe("yes");
    expect(formatCockpitOk(false)).toBe("no");
    expect(formatCockpitOk(null)).toBe("—");
    expect(formatCockpitOk(undefined)).toBe("—");
  });
});
