import { describe, expect, it } from "vitest";
import {
  classifyOperationalStatus,
  classifyProviderClassifiedStatus,
  evidenceRegistryHasPathHint,
  readinessBlockerRows,
  readinessCheckRows,
  workboardQueueItemCount,
} from "./payload-utils";

describe("classifyOperationalStatus", () => {
  it("maps known healthy states to ok", () => {
    expect(classifyOperationalStatus("READY")).toBe("ok");
    expect(classifyOperationalStatus("alive")).toBe("neutral");
  });

  it("maps blocked states to bad", () => {
    expect(classifyOperationalStatus("BLOCKED")).toBe("bad");
  });

  it("maps pending to warn", () => {
    expect(classifyOperationalStatus("PENDING_KEY")).toBe("warn");
  });

  it("maps robustness gate labels", () => {
    expect(classifyOperationalStatus("PROVEN")).toBe("ok");
    expect(classifyOperationalStatus("NOT_APPLICABLE")).toBe("warn");
    expect(classifyOperationalStatus("WARNING")).toBe("warn");
  });

  it("maps evidence strip trust and chain labels", () => {
    expect(classifyOperationalStatus("VERIFIED")).toBe("ok");
    expect(classifyOperationalStatus("UNVERIFIED")).toBe("warn");
    expect(classifyOperationalStatus("CHAIN_OK")).toBe("ok");
    expect(classifyOperationalStatus("CHAIN_DEGRADED")).toBe("bad");
    expect(classifyOperationalStatus("CHAIN_ISSUES")).toBe("bad");
    expect(classifyOperationalStatus("LEDGER_OK")).toBe("ok");
  });
});

describe("classifyProviderClassifiedStatus", () => {
  it("classifies OK and rate limits", () => {
    expect(classifyProviderClassifiedStatus("OK")).toBe("ok");
    expect(classifyProviderClassifiedStatus("RATE_LIMITED")).toBe("bad");
    expect(classifyProviderClassifiedStatus("PENDING_KEY")).toBe("warn");
  });
});

describe("readinessCheckRows", () => {
  it("handles boolean check values", () => {
    const rows = readinessCheckRows({ mutation_routes_safe: true, environment_overrides_valid: false });
    expect(rows).toEqual(
      expect.arrayContaining([
        { key: "mutation_routes_safe", ok: true, detail: "" },
        { key: "environment_overrides_valid", ok: false, detail: "" },
      ]),
    );
  });

  it("handles nested objects", () => {
    const rows = readinessCheckRows({ foo: { ok: false, detail: "nope" } });
    expect(rows[0]).toEqual({ key: "foo", ok: false, detail: "nope" });
  });
});

describe("readinessBlockerRows", () => {
  it("parses blocker objects", () => {
    const rows = readinessBlockerRows([
      { code: "X", message: "bad", remediation_hint: "fix" },
      { not: "valid" },
    ]);
    expect(rows).toEqual([{ code: "X", message: "bad", remediation: "fix" }]);
  });
});

describe("workboardQueueItemCount", () => {
  it("prefers entries length", () => {
    expect(workboardQueueItemCount({ queue: { entries: [{}, {}], work_item_count: 99 } })).toBe(2);
  });

  it("falls back to work_item_count", () => {
    expect(workboardQueueItemCount({ queue: { work_item_count: 3 } })).toBe(3);
  });
});

describe("evidenceRegistryHasPathHint", () => {
  it("finds substring in artifact paths", () => {
    expect(evidenceRegistryHasPathHint([{ path: "/tmp/API_SMOKE_report.json" }], "smoke")).toBe(true);
    expect(evidenceRegistryHasPathHint([{ path: "/tmp/other.json" }], "smoke")).toBe(false);
  });
});
