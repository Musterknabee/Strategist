import { readFileSync } from "fs";
import { join } from "path";
import { describe, expect, it } from "vitest";
import type { UiFacadeRoute } from "../api/types";
import contract from "./ui-facade-routes.json";

const repoRoot = join(__dirname, "..", "..", "..", "..");
const backendFacadePath = join(repoRoot, "docs", "api", "ui-public-facade.snapshot.json");

describe("ui-facade-routes.json (backend-derived contract)", () => {
  it("matches docs/api/ui-public-facade.snapshot.json route digest", () => {
    const backend = JSON.parse(readFileSync(backendFacadePath, "utf8")) as {
      routes_sha256: string;
      route_count: number;
    };
    expect(contract.routes_sha256).toBe(backend.routes_sha256);
    expect(contract.route_count).toBe(backend.route_count);
  });

  it("satisfies UiFacadeRoute[] shape and read/mutation auth invariants", () => {
    expect(contract.schema_version).toBe("ui_facade_frontend_routes_contract/v1");
    expect(Array.isArray(contract.routes)).toBe(true);
    expect(contract.route_count).toBe(contract.routes.length);

    const routes = contract.routes as UiFacadeRoute[];
    for (const r of routes) {
      expect(typeof r.method).toBe("string");
      expect(typeof r.path).toBe("string");
      expect(typeof r.kind).toBe("string");
      expect(typeof r.auth_required).toBe("boolean");
      expect(typeof r.payload_schema).toBe("string");
      expect(r.payload_schema.trim().length).toBeGreaterThan(0);
      const m = r.method.toUpperCase();
      if (m === "GET" || m === "HEAD" || m === "OPTIONS") {
        expect(r.auth_required).toBe(false);
      }
    }

    const postAuthed = routes.filter((r) => r.method === "POST" && r.auth_required);
    expect(postAuthed).toHaveLength(3);
    const postPaths = new Set(postAuthed.map((r) => r.path));
    expect(postPaths.has("/ui/commands/{action}")).toBe(true);
    expect(postPaths.has("/ui/strategy-intake")).toBe(true);
    expect(postPaths.has("/ui/research-cycle/trigger")).toBe(true);
    for (const r of postAuthed) {
      expect(r.kind).toBe("mutation");
    }
  });
});
