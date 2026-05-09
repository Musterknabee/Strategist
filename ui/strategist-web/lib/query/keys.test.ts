import { describe, expect, it } from "vitest";
import { queryKeys } from "./keys";

describe("queryKeys", () => {
  it("uses distinct keys for runtime roles", () => {
    expect(queryKeys.uiRuntime("operator")).not.toEqual(queryKeys.uiRuntime("other"));
  });

  it("uses distinct probe keys", () => {
    expect(queryKeys.probeHealthz).not.toEqual(queryKeys.probeLivez);
    expect(queryKeys.probeReadyz).not.toEqual(queryKeys.probeApiRoot);
    expect(queryKeys.readinessDeployment).not.toEqual(queryKeys.probeReadyz);
  });

  it("uses distinct semantic validator handoff lineage keys", () => {
    expect(queryKeys.uiSemanticValidatorHandoff).not.toEqual(queryKeys.uiSemanticValidatorHandoffLineage);
    expect(queryKeys.uiSemanticValidatorHandoffLineage).not.toEqual(queryKeys.uiSemanticValidatorHandoffLineageFiltered({ chainStatus: "READY" }));
  });

  it("uses distinct paper tracking keys", () => {
    expect(queryKeys.uiPaperTrackingLatest).not.toEqual(queryKeys.uiPaperTrackingDetail("a"));
    expect(queryKeys.uiPaperTrackingDetail("a")).not.toEqual(queryKeys.uiPaperTrackingDetail("b"));
  });

  it("uses distinct workboard board labels", () => {
    expect(queryKeys.uiWorkboard("operator")).not.toEqual(queryKeys.uiWorkboard("other"));
  });

  it("uses distinct evidence keys for search roots", () => {
    expect(queryKeys.uiEvidence(undefined)).not.toEqual(queryKeys.uiEvidence("/a"));
    expect(queryKeys.uiEvidence("/a")).not.toEqual(queryKeys.uiEvidence("/b"));
  });
});
