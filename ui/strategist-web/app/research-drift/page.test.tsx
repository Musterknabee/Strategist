import { describe, expect, it } from "vitest";

import ResearchDriftPage from "./page";

describe("ResearchDriftPage", () => {
  it("exports a page component", () => {
    expect(ResearchDriftPage).toBeTypeOf("function");
  });
});
