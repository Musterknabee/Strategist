import { describe, expect, it } from "vitest";
import { deriveWorkboardDegradedReason, type UiWorkboardPayload } from "./types";

const basePayload = (): UiWorkboardPayload => ({
  schema_version: "ui_workboard_dashboard/v1",
  generated_at_utc: "2026-01-01T00:00:00Z",
  board_label: "operator",
  queue: {},
  pack_workbench: {},
  transition_policy: {},
  intelligence: {},
  materialization: {},
  stats: {
    active_count: 0,
    governed_count: 0,
    journaled_count: 0,
    escalated_count: 0,
    blocked_count: 0,
    linked_count: 0,
    stale_link_count: 0,
    pack_item_count: 0,
    pack_column_count: 0,
    freshness_state: "FRESH",
  },
});

describe("deriveWorkboardDegradedReason", () => {
  it("returns null when healthy", () => {
    expect(deriveWorkboardDegradedReason(basePayload())).toBeNull();
  });

  it("flags stale freshness", () => {
    const p = basePayload();
    p.stats.freshness_state = "STALE";
    expect(deriveWorkboardDegradedReason(p)).toContain("STALE");
  });
});
