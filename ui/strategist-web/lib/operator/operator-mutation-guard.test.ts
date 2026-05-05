import { describe, expect, it } from "vitest";
import {
  mutationRequiresBrowserToken,
  mutationSurfaceAllowed,
  parseMutationSafety,
} from "./operator-mutation-guard";

describe("parseMutationSafety", () => {
  it("returns null when authorization_mode is missing", () => {
    expect(parseMutationSafety({ runtime_mode: "DEV" })).toBeNull();
    expect(parseMutationSafety(null)).toBeNull();
  });

  it("parses a well-formed mutation_safety object", () => {
    const ms = parseMutationSafety({
      runtime_mode: "DEV",
      authorization_mode: "NON_PRODUCTION_BYPASS",
      token_configured: false,
      mutation_routes_safe: true,
      detail_code: "REMOTE_NON_PRODUCTION_MUTATION_BYPASS_ENABLED",
    });
    expect(ms?.authorization_mode).toBe("NON_PRODUCTION_BYPASS");
    expect(ms?.mutation_routes_safe).toBe(true);
  });
});

describe("mutationSurfaceAllowed", () => {
  it("fails closed when safety is unknown", () => {
    const r = mutationSurfaceAllowed(null);
    expect(r.ok).toBe(false);
    expect(r.reason).toBe("MUTATION_SAFETY_UNKNOWN");
  });

  it("blocks when mutation routes are not safe", () => {
    const r = mutationSurfaceAllowed({
      runtime_mode: "PRODUCTION",
      authorization_mode: "TOKEN_PROTECTED",
      token_configured: true,
      mutation_routes_safe: false,
      detail_code: "MUTATION_ROUTES_UNSAFE",
    });
    expect(r.ok).toBe(false);
    expect(r.reason).toBe("MUTATION_ROUTES_UNSAFE");
  });

  it("allows when routes are safe", () => {
    const r = mutationSurfaceAllowed({
      runtime_mode: "DEV",
      authorization_mode: "NON_PRODUCTION_BYPASS",
      token_configured: false,
      mutation_routes_safe: true,
      detail_code: "REMOTE_NON_PRODUCTION_MUTATION_BYPASS_ENABLED",
    });
    expect(r.ok).toBe(true);
  });
});

describe("mutationRequiresBrowserToken", () => {
  it("is false when safety is null or routes unsafe", () => {
    expect(mutationRequiresBrowserToken(null)).toBe(false);
    expect(
      mutationRequiresBrowserToken({
        runtime_mode: "PRODUCTION",
        authorization_mode: "TOKEN_PROTECTED",
        token_configured: true,
        mutation_routes_safe: false,
        detail_code: "X",
      }),
    ).toBe(false);
  });

  it("is true for TOKEN_PROTECTED with safe routes", () => {
    expect(
      mutationRequiresBrowserToken({
        runtime_mode: "PRODUCTION",
        authorization_mode: "TOKEN_PROTECTED",
        token_configured: true,
        mutation_routes_safe: true,
        detail_code: "MUTATION_TOKEN_CONFIGURED",
      }),
    ).toBe(true);
  });
});
