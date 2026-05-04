import { describe, expect, it } from "vitest";
import { normalizeStrategistApiBaseUrl, StrategistConfigError } from "./public-config";

describe("normalizeStrategistApiBaseUrl", () => {
  it("trims and strips trailing slashes", () => {
    expect(normalizeStrategistApiBaseUrl("  https://ops.example.com/api/  ")).toBe(
      "https://ops.example.com/api",
    );
  });

  it("rejects non-http protocols", () => {
    expect(() => normalizeStrategistApiBaseUrl("ftp://x")).toThrow(StrategistConfigError);
  });

  it("rejects empty", () => {
    expect(() => normalizeStrategistApiBaseUrl("")).toThrow(StrategistConfigError);
  });
});
