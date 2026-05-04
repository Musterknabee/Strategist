import { describe, expect, it } from "vitest";
import pageSource from "./page.tsx?raw";

describe("research handoff signoff page", () => {
  it("renders handoff verification without deployment or order controls", () => {
    expect(pageSource).toContain("Research Handoff Signoff");
    expect(pageSource).toContain("not DEPLOYMENT_APPROVED");
    expect(pageSource).toContain("/ui/research-os/handoff-signoff/latest");
    expect(pageSource.toLowerCase()).not.toContain("place order");
    expect(pageSource.toLowerCase()).not.toContain("submit order");
  });
});
