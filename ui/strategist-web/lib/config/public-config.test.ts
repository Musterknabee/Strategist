import { describe, expect, it } from "vitest";
import { isStrategistDemoModeEnabled, normalizeStrategistApiBaseUrl, StrategistConfigError } from "./public-config";

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

describe("isStrategistDemoModeEnabled", () => {
  it("is disabled by default", () => {
    delete process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE;
    expect(isStrategistDemoModeEnabled()).toBe(false);
  });

  it("is enabled only by explicit true", () => {
    process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE = "true";
    expect(isStrategistDemoModeEnabled()).toBe(true);
    process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE = "false";
    expect(isStrategistDemoModeEnabled()).toBe(false);
    delete process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE;
  });
});
