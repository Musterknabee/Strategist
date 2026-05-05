import { readFileSync } from "fs";
import { join } from "path";
import { describe, expect, it } from "vitest";
import contractJson from "./ui-facade-contract.json";
import { listUiFacadeRoutes, uiFacadeContract } from "./ui-facade-contract";

const repoRoot = join(__dirname, "..", "..", "..", "..");
const snapshotPath = join(repoRoot, "docs", "api", "ui-public-facade.snapshot.json");

describe("lib/generated/ui-facade-contract (backend snapshot mirror)", () => {
  it("imports and exposes the same route digest as docs/api/ui-public-facade.snapshot.json", () => {
    const snap = JSON.parse(readFileSync(snapshotPath, "utf8")) as {
      routes_sha256: string;
      route_count: number;
      schema_version: string;
    };
    expect(uiFacadeContract.routes_sha256).toBe(snap.routes_sha256);
    expect(uiFacadeContract.route_count).toBe(snap.route_count);
    expect(uiFacadeContract.source_snapshot_schema_version).toBe(snap.schema_version);
    expect(contractJson.routes_sha256).toBe(snap.routes_sha256);
  });

  it("includes the metadata facade route with a non-empty payload_schema", () => {
    const routes = listUiFacadeRoutes();
    const facade = routes.find((r) => r.path === "/ui/facade" && r.method === "GET");
    expect(facade).toBeDefined();
    expect(facade?.kind).toBe("metadata");
    expect(facade?.auth_required).toBe(false);
    expect(facade?.payload_schema?.trim().length).toBeGreaterThan(0);
  });

  it("marks POST mutation routes as auth_required", () => {
    const posts = listUiFacadeRoutes().filter((r) => r.method === "POST");
    expect(posts.length).toBeGreaterThan(0);
    for (const p of posts) {
      expect(p.auth_required).toBe(true);
      expect(p.kind).toBe("mutation");
      expect(p.payload_schema.trim().length).toBeGreaterThan(0);
    }
  });
});
