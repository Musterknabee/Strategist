import { describe, expect, it } from "vitest";
import { StrategistApiError } from "@/lib/api/strategist-errors";
import { readPlaneRetry } from "./read-plane-query";

describe("readPlaneRetry", () => {
  it("stops after two attempts", () => {
    expect(readPlaneRetry(2, new Error("transient"))).toBe(false);
  });

  it("does not retry unauthorized StrategistApiError", () => {
    const err = new StrategistApiError("nope", 401, undefined, "unauthorized");
    expect(readPlaneRetry(0, err)).toBe(false);
  });

  it("does not retry other 4xx responses", () => {
    expect(readPlaneRetry(0, new StrategistApiError("bad", 404))).toBe(false);
  });

  it("retries 5xx until the configured failure cap", () => {
    const err = new StrategistApiError("unavailable", 503);
    expect(readPlaneRetry(0, err)).toBe(true);
    expect(readPlaneRetry(1, err)).toBe(true);
    expect(readPlaneRetry(2, err)).toBe(false);
  });

  it("retries generic errors until the configured failure cap", () => {
    const err = new TypeError("fetch failed");
    expect(readPlaneRetry(0, err)).toBe(true);
    expect(readPlaneRetry(1, err)).toBe(true);
    expect(readPlaneRetry(2, err)).toBe(false);
  });
});
