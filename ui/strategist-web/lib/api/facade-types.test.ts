import { describe, expect, it } from "vitest";
import type { UiFacadePayload } from "./types";

describe("UiFacadePayload (facade contract)", () => {
  it("accepts extended backend fields from GET /ui/facade", () => {
    const p: UiFacadePayload = {
      schema_version: "ui_public_facade_inventory/v1",
      surface: "ui",
      frontend_expected_package: "ui/strategist-web",
      frontend_package_present: false,
      frontend_package_detected_by_backend: false,
      frontend_readiness_claimed: false,
      frontend_runtime_reachable: null,
      frontend_operator_console_hint: "API-only containers: expected false for package flags.",
      read_plane_only: true,
      mutation_route: "/ui/commands/{action}",
      routes: [],
    };
    expect(p.frontend_package_present).toBe(false);
    expect(p.frontend_runtime_reachable).toBeNull();
  });
});
