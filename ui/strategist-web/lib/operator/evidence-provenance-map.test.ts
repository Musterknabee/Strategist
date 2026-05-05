import { describe, expect, it } from "vitest";
import {
  chainIntegrityLabel,
  normalizeEvidenceField,
  normalizeTrustVerificationForBadge,
  projectionVerifiedLabel,
} from "./evidence-provenance-map";

describe("normalizeEvidenceField", () => {
  it("returns PENDING for empty input", () => {
    expect(normalizeEvidenceField(undefined)).toBe("PENDING");
    expect(normalizeEvidenceField("")).toBe("PENDING");
  });

  it("uppercases trimmed strings", () => {
    expect(normalizeEvidenceField("  ok  ")).toBe("OK");
  });
});

describe("normalizeTrustVerificationForBadge", () => {
  it("maps verification tokens for StatusBadge", () => {
    expect(normalizeTrustVerificationForBadge(undefined)).toBe("PENDING");
    expect(normalizeTrustVerificationForBadge("verified")).toBe("VERIFIED");
    expect(normalizeTrustVerificationForBadge("UNVERIFIED")).toBe("UNVERIFIED");
    expect(normalizeTrustVerificationForBadge("CHAIN_OK")).toBe("CHAIN_OK");
  });
});

describe("projectionVerifiedLabel", () => {
  it("maps booleans", () => {
    expect(projectionVerifiedLabel(true)).toBe("VERIFIED");
    expect(projectionVerifiedLabel(false)).toBe("UNVERIFIED");
    expect(projectionVerifiedLabel(null)).toBe("PENDING");
  });
});

describe("chainIntegrityLabel", () => {
  it("prefers explicit chain_ok false", () => {
    expect(chainIntegrityLabel(false, 0)).toBe("CHAIN_DEGRADED");
  });

  it("reports issues when count positive", () => {
    expect(chainIntegrityLabel(undefined, 2)).toBe("CHAIN_ISSUES");
    expect(chainIntegrityLabel(true, 1)).toBe("CHAIN_ISSUES");
  });

  it("returns CHAIN_OK when healthy", () => {
    expect(chainIntegrityLabel(true, 0)).toBe("CHAIN_OK");
  });

  it("returns UNKNOWN when inconclusive", () => {
    expect(chainIntegrityLabel(undefined, 0)).toBe("UNKNOWN");
  });
});
