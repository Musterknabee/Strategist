import { describe, expect, it } from "vitest";
import pageSource from "./page.tsx?raw";

describe("research handoff page", () => {
  it("renders handoff posture without deployment or order controls", () => {
    expect(pageSource).toContain("Research Handoff");
    expect(pageSource).toContain("not DEPLOYMENT_APPROVED");
    expect(pageSource).toContain("/ui/research-os/handoff/latest");
    expect(pageSource.toLowerCase()).not.toContain("place order");
    expect(pageSource.toLowerCase()).not.toContain("submit order");
  });
});
