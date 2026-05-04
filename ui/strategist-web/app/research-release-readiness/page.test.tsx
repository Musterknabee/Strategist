import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";

describe("research release readiness page", () => {
  it("renders read-plane copy and no order controls", () => {
    const src = fs.readFileSync(path.join(process.cwd(), "app/research-release-readiness/page.tsx"), "utf8");
    expect(src).toContain("Research Release Readiness");
    expect(src).toContain("not deployment approval");
    expect(src).toContain("/ui/research-os/release-readiness/latest");
    expect(src.toLowerCase()).not.toContain("submit order");
    expect(src.toLowerCase()).not.toContain("place order");
  });
});
