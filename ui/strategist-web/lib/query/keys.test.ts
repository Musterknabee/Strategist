import { describe, expect, it } from "vitest";
import { queryKeys } from "./keys";

describe("queryKeys", () => {
  it("uses distinct keys for runtime roles", () => {
    expect(queryKeys.uiRuntime("operator")).not.toEqual(queryKeys.uiRuntime("other"));
  });

  it("uses distinct probe keys", () => {
    expect(queryKeys.probeHealthz).not.toEqual(queryKeys.probeLivez);
    expect(queryKeys.probeReadyz).not.toEqual(queryKeys.probeApiRoot);
  });
});
