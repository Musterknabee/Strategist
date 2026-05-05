/** @vitest-environment node */

import { describe, expect, it } from "vitest";
import {
  buildRemediationGovernanceItems,
  unwrapApiPayload,
  type RemediationGovernanceInput,
} from "./remediation-governance-model";

function base(overrides: Partial<RemediationGovernanceInput> = {}): RemediationGovernanceInput {
  const d: RemediationGovernanceInput = {
    readyzBody: { status: "READY", blockers: [], warnings: [], checked_at_utc: "2026-05-04T12:00:00Z" },
    readyzLoading: false,
    readyzError: false,
    deployment: { generated_at_utc: "2026-05-04T12:00:00Z", blocker_codes: [], warning_codes: [] },
    deploymentLoading: false,
    deploymentError: false,
    policyGatePayload: {
      schema_version: "ui_research_os_policy_gate/v1",
      generated_at_utc: "2026-05-04T12:00:00Z",
      degraded: [],
      latest: {
        gate_id: "g1",
        decision: "PASS",
        blockers: [],
        warnings: [],
        rules: [],
        manifest_sha256: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        trust_banner: "TRUSTED",
      },
    },
    policyGateLoading: false,
    policyGateError: false,
    exceptionPayload: { schema_version: "x", generated_at_utc: "2026-05-04T12:00:00Z", degraded: [], latest: null },
    exceptionLoading: false,
    exceptionError: false,
    remediationPayload: { schema_version: "x", generated_at_utc: "2026-05-04T12:00:00Z", degraded: [], latest: null },
    remediationLoading: false,
    remediationError: false,
    drift: { generated_at_utc: "2026-05-04T12:00:00Z", degraded: [] },
    driftLoading: false,
    driftError: false,
    releaseReadiness: { status: "PRESENT", degraded: [], generated_at_utc: "2026-05-04T12:00:00Z" },
    releaseLoading: false,
    releaseError: false,
    reviewJournal: { schema_version: "x", generated_at_utc: "2026-05-04T12:00:00Z", latest: { status: "OK", blockers: [] } },
    reviewJournalLoading: false,
    reviewJournalError: false,
    providerStaleCount: null,
    providerBlockedCount: null,
  };
  return { ...d, ...overrides };
}

describe("unwrapApiPayload", () => {
  it("unwraps nested { data: payload } envelopes", () => {
    const r = unwrapApiPayload({
      status: 200,
      data: { schema_version: "ui_x/v1", latest: null, degraded: [] },
    });
    expect(r?.schema_version).toBe("ui_x/v1");
  });
});

describe("buildRemediationGovernanceItems", () => {
  it("marks readiness blocker CRITICAL when no governed exception applies", () => {
    const r = buildRemediationGovernanceItems(
      base({
        readyzBody: {
          status: "READY",
          blockers: ["LEDGER_PATH"],
          warnings: [],
          checked_at_utc: "2026-05-04T12:00:00Z",
        },
      }),
    );
    const row = r.items.find((i) => i.item_id === "readyz:blocker:0");
    expect(row?.severity).toBe("CRITICAL");
    expect(row?.exception_semantics).toBe("NO_EXCEPTION");
  });

  it("keeps readiness blocker visible but WARNING when exception covers residual", () => {
    const r = buildRemediationGovernanceItems(
      base({
        readyzBody: {
          status: "READY",
          blockers: ["LEDGER_PATH"],
          warnings: [],
          checked_at_utc: "2026-05-04T12:00:00Z",
        },
        exceptionPayload: {
          schema_version: "x",
          generated_at_utc: "2026-05-04T12:00:00Z",
          degraded: [],
          latest: {
            exception_id: "ex-1",
            status: "ACTIVE",
            expires_at_utc: "2099-01-01T00:00:00Z",
            constraints: ["paper-only"],
            trust_banner: "TRUSTED",
            operator_id: "op-1",
            residual_blockers: ["LEDGER_PATH"],
          },
        },
      }),
    );
    const row = r.items.find((i) => i.item_id === "readyz:blocker:0");
    expect(row?.exception_semantics).toBe("EXCEPTION_ACTIVE");
    expect(row?.severity).toBe("WARNING");
  });

  it("treats expired governed exception as CRITICAL on exception summary", () => {
    const r = buildRemediationGovernanceItems(
      base({
        exceptionPayload: {
          schema_version: "x",
          generated_at_utc: "2026-05-04T12:00:00Z",
          degraded: [],
          latest: {
            exception_id: "ex-1",
            status: "ACTIVE",
            expires_at_utc: "2020-01-01T00:00:00Z",
            constraints: ["c1"],
            trust_banner: "TRUSTED",
            operator_id: "op-1",
            residual_blockers: [],
          },
        },
      }),
    );
    const row = r.items.find((i) => i.item_id === "exception:summary");
    expect(row?.exception_semantics).toBe("EXCEPTION_EXPIRED");
    expect(row?.severity).toBe("CRITICAL");
  });

  it("flags remediation complete with untrusted banner as REMEDIATION_UNVERIFIED (WARNING plan row)", () => {
    const r = buildRemediationGovernanceItems(
      base({
        remediationPayload: {
          schema_version: "x",
          generated_at_utc: "2026-05-04T12:00:00Z",
          degraded: [],
          latest: {
            plan_id: "p1",
            status: "COMPLETE",
            trust_banner: "UNVERIFIED",
            item_count: 0,
            recommended_next_actions: [],
          },
        },
      }),
    );
    const row = r.items.find((i) => i.item_id === "remediation:plan");
    expect(row?.remediation_semantics).toBe("REMEDIATION_UNVERIFIED");
    expect(row?.severity).toBe("WARNING");
  });

  it("exposes digest prefix when policy gate manifest hash exists", () => {
    const withBlock = buildRemediationGovernanceItems(
      base({
        policyGatePayload: {
          schema_version: "x",
          generated_at_utc: "2026-05-04T12:00:00Z",
          degraded: [],
          latest: {
            gate_id: "g1",
            decision: "BLOCK",
            blockers: ["RULE_FAIL"],
            manifest_sha256: "fedcba0123456789fedcba0123456789fedcba0123456789fedcba0123456789",
            rules: [],
          },
        },
      }),
    );
    const b = withBlock.items.find((i) => i.item_id === "policy:blocker:0");
    expect(b?.evidence_digest_prefix).toMatch(/^fedcba012345/);
  });
});
