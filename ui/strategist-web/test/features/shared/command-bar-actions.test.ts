import { describe, expect, it } from "vitest";

import { filterCommandBarActions, getVisibleCommandBarActions } from "@/features/shared/command-bar-actions";

describe("command-bar-actions", () => {
  it("filters route actions by allowed domains while retaining shell actions", () => {
    const actions = getVisibleCommandBarActions(["validator", "evidence"]);
    const ids = actions.map((action) => action.id);
    expect(ids).toContain("route-burnin");
    expect(ids).toContain("route-evidence");
    expect(ids).not.toContain("route-workboard");
    expect(ids).toContain("shell-open-latest-receipt");
  });

  it("matches actions using label, description, and keyword text", () => {
    const actions = getVisibleCommandBarActions(["control-plane", "validator", "evidence", "tribunal"]);
    expect(filterCommandBarActions(actions, "forensic").map((action) => action.id)).toContain("route-forensic");
    expect(filterCommandBarActions(actions, "alpaca").map((action) => action.id)).toContain("route-providers");
    expect(filterCommandBarActions(actions, "latest receipt").map((action) => action.id)).toContain("shell-open-latest-receipt");
  });
});
