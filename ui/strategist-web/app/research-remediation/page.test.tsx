import { describe, expect, it } from "vitest";

import Page from "./page";

describe("ResearchRemediationPage", () => {
  it("exports a page component", () => {
    expect(Page).toBeTypeOf("function");
  });
});
